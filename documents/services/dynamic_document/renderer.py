from copy import deepcopy
from io import BytesIO
import re

from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.table import _Row
from django.core.exceptions import ValidationError

from .markers import TOKEN_PATTERN, inspect_docx
from .validator import validate_template


def render_document(content, structure, context, catalog):
    validated = validate_template(content, structure, catalog)
    document = validated.scan.document
    zone_rows = {}

    for zone in validated.definition.zones:
        pair = validated.scan.marker_pairs[zone.marker_pair - 1]
        zone_rows[pair.start.row] = (zone, pair)

    for row_xml, (zone, pair) in list(zone_rows.items()):
        row = _Row(row_xml, _table_wrapper(pair.start.paragraph))
        items = _resolve_path(context, zone.collection)
        if items is None:
            items = []
        if not isinstance(items, (list, tuple)):
            raise ValidationError(
                f"La collection « {zone.collection} » n’est pas une liste."
            )
        parent = row._tr.getparent()
        template_row = deepcopy(row._tr)
        for item in items:
            clone = deepcopy(template_row)
            row._tr.addprevious(clone)
            rendered_row = _Row(clone, row.table)
            row_context = dict(context)
            row_context[zone.item_name] = item
            for paragraph in _iter_row_paragraphs(rendered_row):
                _replace_tokens(paragraph, row_context)
        parent.remove(row._tr)

    collection_bindings = _collection_bindings(catalog)
    automatic_row_ids = set()
    if not validated.definition.zones:
        automatic_row_ids = _expand_collection_rows(
            validated.scan,
            context,
            collection_bindings,
        )

    zone_row_ids = set(zone_rows)
    for _, paragraph in validated.scan.paragraphs:
        if paragraph._p.getparent() is None or _belongs_to_zone_row(
            paragraph,
            zone_row_ids | automatic_row_ids,
        ):
            continue
        _replace_tokens(paragraph, context, collection_bindings)

    output = BytesIO()
    document.save(output)
    generated = output.getvalue()
    final_scan = inspect_docx(generated)
    if final_scan.markers or final_scan.variables:
        remaining = sorted({item.name for item in final_scan.variables})
        if remaining:
            raise ValidationError(
                "Des variables restent non résolues dans le document généré : "
                f"{', '.join(remaining)}."
            )
        raise ValidationError(
            "Des marqueurs de zone restent présents dans le document généré."
        )
    return generated


def _collection_bindings(catalog):
    bindings = {}
    for collection_path, collection in catalog.collections.items():
        item_name = collection["item_name"]
        previous_path = bindings.setdefault(item_name, collection_path)
        if previous_path != collection_path:
            raise ValidationError(
                f"item_name « {item_name} » ne peut pas désigner plusieurs "
                "collections."
            )
    return bindings


def _expand_collection_rows(scan, context, collection_bindings):
    candidates = {}
    for occurrence in scan.variables:
        binding = _collection_binding(occurrence.name, collection_bindings)
        if binding is None or occurrence.row is None:
            continue
        item_name, collection_path = binding
        candidate = candidates.setdefault(
            occurrence.row,
            {"bindings": set(), "paragraph": occurrence.paragraph},
        )
        candidate["bindings"].add((item_name, collection_path))

    automatic_rows = {}
    for row_xml, candidate in candidates.items():
        if len(candidate["bindings"]) != 1:
            raise ValidationError(
                "Une ligne de tableau ne peut répéter qu’une seule collection."
            )
        binding = next(iter(candidate["bindings"]))
        has_repeating_ancestor = any(
            ancestor_xml is not row_xml
            and _row_is_within(row_xml, ancestor_xml)
            and binding in ancestor["bindings"]
            for ancestor_xml, ancestor in candidates.items()
        )
        if not has_repeating_ancestor:
            automatic_rows[row_xml] = (binding, candidate["paragraph"])

    for row_xml, ((item_name, collection_path), paragraph) in automatic_rows.items():
        row = _Row(row_xml, _table_wrapper(paragraph))
        items = _resolve_path(context, collection_path)
        if items is None:
            items = []
        if not isinstance(items, (list, tuple)):
            raise ValidationError(
                f"La collection « {collection_path} » n’est pas une liste."
            )

        parent = row._tr.getparent()
        template_row = deepcopy(row._tr)
        for item in items:
            clone = deepcopy(template_row)
            row._tr.addprevious(clone)
            rendered_row = _Row(clone, row.table)
            row_context = dict(context)
            row_context[item_name] = item
            for paragraph in _iter_row_paragraphs(rendered_row):
                _replace_tokens(paragraph, row_context, collection_bindings)
        parent.remove(row._tr)

    return set(automatic_rows)


def _table_wrapper(paragraph):
    from docx.table import Table

    current = paragraph._p.getparent()
    while current is not None and not current.tag.endswith("}tbl"):
        current = current.getparent()
    if current is None:
        raise ValidationError("La ligne répétitive n’appartient pas à un tableau.")
    return Table(current, paragraph._parent)


def _belongs_to_zone_row(paragraph, zone_row_ids):
    current = paragraph._p.getparent()
    while current is not None:
        if current.tag.endswith("}tr") and current in zone_row_ids:
            return True
        current = current.getparent()
    return False


def _row_is_within(row, target_row):
    current = row
    while current is not None:
        if current is target_row:
            return True
        current = current.getparent()
        while current is not None and not current.tag.endswith("}tr"):
            current = current.getparent()
    return False


def _iter_row_paragraphs(row):
    seen_cells = set()
    for cell in row.cells:
        if id(cell._tc) in seen_cells:
            continue
        seen_cells.add(id(cell._tc))
        yield from _iter_cell_paragraphs(cell)


def _iter_cell_paragraphs(cell):
    yield from cell.paragraphs
    for table in cell.tables:
        for nested_row in table.rows:
            yield from _iter_row_paragraphs(nested_row)


def _replace_tokens(paragraph, context, collection_bindings=None):
    text_nodes = paragraph._p.xpath(".//w:t")
    text = "".join(node.text or "" for node in text_nodes)
    matches = list(TOKEN_PATTERN.finditer(text))
    if not matches:
        return

    offsets = []
    offset = 0
    for node in text_nodes:
        offsets.append(offset)
        offset += len(node.text or "")

    for match in reversed(matches):
        name = match.group(1).strip()
        if name in {"debut", "fin"}:
            replacement = ""
        else:
            binding = _collection_binding(name, collection_bindings or {})
            if binding is not None and binding[0] not in context:
                item_name, collection_path = binding
                items = _resolve_path(context, collection_path)
                if items is None:
                    items = []
                if not isinstance(items, (list, tuple)):
                    raise ValidationError(
                        f"La collection « {collection_path} » n’est pas une liste."
                    )
                replacement = "\n".join(
                    _format(_resolve_path({item_name: item}, name), name)
                    for item in items
                )
            else:
                replacement = _format(_resolve_path(context, name), name)
        start, end = match.span()
        intersecting = [
            index
            for index, node_start in enumerate(offsets)
            if node_start < end and node_start + len(text_nodes[index].text or "") > start
        ]
        if not intersecting:
            raise ValidationError(
                f"La variable « {name} » ne peut pas être remplacée."
            )

        first, last = intersecting[0], intersecting[-1]
        first_local = start - offsets[first]
        first_node = text_nodes[first]
        prefix = (first_node.text or "")[:first_local]
        suffix = (text_nodes[last].text or "")[end - offsets[last] :]
        if first == last:
            suffix = (first_node.text or "")[end - offsets[first] :]
        _insert_formatted_text(
            first_node,
            prefix,
            replacement,
            suffix if first == last else "",
        )
        if first == last:
            continue

        _preserve_spaces(first_node)
        for index in range(first + 1, last):
            text_nodes[index].text = ""
        last_node = text_nodes[last]
        last_node.text = suffix
        _preserve_spaces(last_node)


def _insert_formatted_text(first_node, prefix, replacement, suffix):
    segments = re.split(r"([\n\t])", replacement)
    first_node.text = prefix + segments[0]
    current = first_node
    for segment in segments[1:]:
        if segment in {"\n", "\t"}:
            marker = OxmlElement("w:br" if segment == "\n" else "w:tab")
            current.addnext(marker)
            current = marker
        else:
            text_node = OxmlElement("w:t")
            text_node.text = segment
            current.addnext(text_node)
            current = text_node

    if suffix:
        if current.tag.endswith("}t"):
            current.text = (current.text or "") + suffix
        else:
            text_node = OxmlElement("w:t")
            text_node.text = suffix
            current.addnext(text_node)
            current = text_node
    _preserve_spaces(first_node)
    if current is not first_node:
        _preserve_spaces(current)


def _preserve_spaces(node):
    text = node.text or ""
    if text.startswith(" ") or text.endswith(" "):
        node.set(qn("xml:space"), "preserve")


def _resolve_path(context, path):
    value = context
    for part in path.split("."):
        if value is None:
            return ""
        if not isinstance(value, dict):
            raise ValidationError(
                f"La valeur intermédiaire de « {path} » n’est pas un objet."
            )
        if part not in value:
            raise ValidationError(
                f"La valeur « {path} » n’a pas été préparée dans le contexte."
            )
        value = value[part]
    return value


def _collection_binding(name, collection_bindings):
    for item_name, collection_path in collection_bindings.items():
        if name.startswith(f"{item_name}."):
            return item_name, collection_path
    return None


def _format(value, variable):
    if value is None:
        return ""
    if isinstance(value, (str, int, float, bool)):
        return str(value)
    raise ValidationError(
        f"La variable « {variable} » contient une valeur non scalaire."
    )
