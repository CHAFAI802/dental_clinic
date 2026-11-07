from django.core.exceptions import ValidationError

from .context import build_context
from .discovery import (
    CollectionExposure,
    ModelCatalog,
    ModelExposure,
    discover_model_catalog,
    get_builtin_catalog,
    get_builtin_catalogs,
    get_builtin_exposures,
    queryset_hints,
)
from .markers import inspect_docx
from .renderer import render_document
from .structure import DocumentDefinition, ZoneDefinition, parse_definition
from .validator import validate_template


def generate_document(
    template,
    instance,
    *,
    exposure=None,
    collection_values=None,
):
    """Render a saved template after the caller authorizes its data objects."""
    structure = getattr(template, "structure_config", None)
    if not structure:
        raise ValidationError(
            "Le modèle documentaire ne possède pas de configuration dynamique."
        )
    if not getattr(template, "file", None):
        raise ValidationError("Le modèle documentaire ne possède pas de fichier DOCX.")

    definition = parse_definition(structure)
    if exposure is None:
        exposure = get_builtin_exposures().get(definition.root_model)
    if exposure is None:
        raise ValidationError(
            f"Aucune exposition autorisée pour « {definition.root_model} »."
        )
    catalog = discover_model_catalog(exposure, definition.root_name)
    try:
        with template.file.open("rb") as source:
            content = source.read()
    except FileNotFoundError as error:
        raise ValidationError(
            "Le fichier DOCX associé au modèle est indisponible."
        ) from error
    scan = inspect_docx(content)
    context = build_context(
        instance,
        definition,
        exposure,
        collection_values=collection_values,
        variables=(occurrence.name for occurrence in scan.variables),
    )
    return render_document(content, definition, context, catalog)


__all__ = [
    "CollectionExposure",
    "DocumentDefinition",
    "ModelCatalog",
    "ModelExposure",
    "ZoneDefinition",
    "build_context",
    "discover_model_catalog",
    "generate_document",
    "get_builtin_catalog",
    "get_builtin_catalogs",
    "get_builtin_exposures",
    "parse_definition",
    "queryset_hints",
    "render_document",
    "validate_template",
]
