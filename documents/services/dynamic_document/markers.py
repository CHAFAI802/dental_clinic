import re
from dataclasses import dataclass
from io import BytesIO
from zipfile import BadZipFile

from docx import Document as WordDocument
from docx.opc.exceptions import PackageNotFoundError
from docx.oxml.table import CT_Tbl
from docx.oxml.text.paragraph import CT_P
from docx.table import Table
from docx.text.paragraph import Paragraph
from django.core.exceptions import ValidationError
from lxml.etree import XMLSyntaxError


TOKEN_PATTERN = re.compile(r"\{\{\s*([^{}]+?)\s*\}\}")
BOUNDARY_MARKERS = {"debut", "fin"}


@dataclass(frozen=True)
class VariableOccurrence:
    name: str
    paragraph: object
    row: object | None
    story: str


@dataclass(frozen=True)
class MarkerOccurrence:
    kind: str
    paragraph: object
    row: object | None
    table: object | None
    story: str


@dataclass(frozen=True)
class MarkerPair:
    index: int
    start: MarkerOccurrence
    end: MarkerOccurrence


@dataclass(frozen=True)
class DocumentScan:
    document: object
    variables: tuple[VariableOccurrence, ...]
    markers: tuple[MarkerOccurrence, ...]
    marker_pairs: tuple[MarkerPair, ...]
    paragraphs: tuple[tuple[str, object], ...]


def inspect_docx(content):
    if not content:
        raise ValidationError("Le fichier DOCX est vide.")
    try:
        document = WordDocument(BytesIO(content))
    except (
        BadZipFile,
        PackageNotFoundError,
        XMLSyntaxError,
        ValueError,
        KeyError,
    ) as error:
        raise ValidationError(
            "Le fichier n’est pas un document DOCX valide ou lisible."
        ) from error

    variables = []
    markers = []
    paragraphs = []
    for story, paragraph in _iter_document_paragraphs(document):
        paragraphs.append((story, paragraph))
        text = _paragraph_text(paragraph)
        matches = list(TOKEN_PATTERN.finditer(text))
        remainder = TOKEN_PATTERN.sub("", text)
        if "{" in remainder or "}" in remainder:
            raise ValidationError(
                f"Marqueur mal formé dans le document ({story})."
            )

        row, table = _containing_row_and_table(paragraph)
        for match in matches:
            name = match.group(1).strip()
            if name in BOUNDARY_MARKERS:
                markers.append(
                    MarkerOccurrence(name, paragraph, row, table, story)
                )
            else:
                variables.append(VariableOccurrence(name, paragraph, row, story))

    if len(markers) % 2:
        last_kind = markers[-1].kind if markers else "debut"
        message = (
            "Le marqueur de fin est absent."
            if last_kind == "debut"
            else "Le marqueur de début est absent."
        )
        raise ValidationError(message)

    marker_pairs = []
    for index in range(0, len(markers), 2):
        start, end = markers[index : index + 2]
        if start.kind != "debut":
            raise ValidationError(
                "Les marqueurs doivent alterner {{ debut }} puis {{ fin }}."
            )
        if end.kind != "fin":
            raise ValidationError("Le marqueur {{ fin }} est absent.")
        marker_pairs.append(MarkerPair(index // 2 + 1, start, end))

    if any(
        marker.kind == "debut" and index + 1 < len(markers)
        and markers[index + 1].kind == "debut"
        for index, marker in enumerate(markers)
    ):
        raise ValidationError("Les zones imbriquées ou ambiguës ne sont pas prises en charge.")

    return DocumentScan(
        document,
        tuple(variables),
        tuple(markers),
        tuple(marker_pairs),
        tuple(paragraphs),
    )


def _paragraph_text(paragraph):
    return "".join(node.text or "" for node in paragraph._p.xpath(".//w:t"))


def _containing_row_and_table(paragraph):
    current = paragraph._p.getparent()
    row = None
    table = None
    while current is not None:
        if row is None and current.tag.endswith("}tr"):
            row = current
        elif table is None and current.tag.endswith("}tbl"):
            table = current
        current = current.getparent()
    return row, table


def _iter_document_paragraphs(document):
    yield from _iter_blocks(document, "body")
    seen_parts = set()
    for section_index, section in enumerate(document.sections):
        for name, part in (
            ("header", section.header),
            ("first_page_header", section.first_page_header),
            ("even_page_header", section.even_page_header),
            ("footer", section.footer),
            ("first_page_footer", section.first_page_footer),
            ("even_page_footer", section.even_page_footer),
        ):
            key = id(part._element)
            if key in seen_parts:
                continue
            seen_parts.add(key)
            yield from _iter_blocks(part, f"{name}-{section_index}")


def _iter_blocks(container, story):
    root = container._element.body if hasattr(container._element, "body") else container._element
    for child in root.iterchildren():
        if isinstance(child, CT_P):
            yield story, Paragraph(child, container)
        elif isinstance(child, CT_Tbl):
            yield from _iter_table_paragraphs(Table(child, container), story)


def _iter_table_paragraphs(table, story):
    seen_cells = set()
    for row in table.rows:
        for cell in row.cells:
            if id(cell._tc) in seen_cells:
                continue
            seen_cells.add(id(cell._tc))
            yield from _iter_cell_paragraphs(cell, story)


def _iter_cell_paragraphs(cell, story):
    for paragraph in cell.paragraphs:
        yield story, paragraph
    for table in cell.tables:
        yield from _iter_table_paragraphs(table, story)
