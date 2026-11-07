from collections.abc import Mapping
from datetime import date, datetime
from decimal import Decimal

from django.core.exceptions import ValidationError
from django.utils import timezone

from .discovery import ModelExposure, discover_model_catalog
from .structure import parse_definition


def build_context(
    instance,
    definition,
    exposure,
    *,
    collection_values=None,
    variables=None,
):
    definition = parse_definition(definition)
    if not isinstance(exposure, ModelExposure):
        raise ValidationError("Une exposition de modèle explicite est requise.")
    if not isinstance(instance, exposure.model):
        raise ValidationError(
            f"L’objet fourni doit être une instance de {exposure.model._meta.label}."
        )

    catalog = discover_model_catalog(exposure, definition.root_name)
    if catalog.root_model != definition.root_model:
        raise ValidationError(
            "L’objet fourni ne correspond pas au modèle racine configuré."
        )
    detected_variables = set(definition.variables)
    if variables is not None:
        detected_variables.update(variables)
    for variable in detected_variables:
        if variable not in catalog.variables:
            raise ValidationError(
                f"La variable « {variable} » n’est pas autorisée par l’exposition."
            )
    for zone in definition.zones:
        collection = catalog.collections.get(zone.collection)
        if collection is None:
            raise ValidationError(
                f"La collection « {zone.collection} » n’est pas autorisée."
            )
        if collection["item_name"] != zone.item_name:
            raise ValidationError(
                f"La zone « {zone.name} » doit utiliser l’élément "
                f"« {collection['item_name']} »."
            )

    variables = detected_variables
    collection_paths = {zone.collection for zone in definition.zones}
    for collection_path, collection in catalog.collections.items():
        item_name = collection["item_name"]
        if any(variable.startswith(f"{item_name}.") for variable in variables):
            collection_paths.add(collection_path)
    if collection_values is not None and not isinstance(collection_values, Mapping):
        raise ValidationError("collection_values doit être un objet de collections.")
    external_values = collection_values or {}
    permitted_overrides = collection_paths
    unexpected_external = set(external_values) - permitted_overrides
    if unexpected_external:
        raise ValidationError(
            "Collections non autorisées : "
            f"{', '.join(sorted(unexpected_external))}."
        )

    data = _build_object(
        instance,
        exposure,
        definition.root_name,
        variables,
        collection_paths,
        external_values,
    )
    return {definition.root_name: data}


def _build_object(instance, exposure, prefix, variables, collection_paths, external_values):
    result = {}

    for field_name in exposure.fields:
        path = f"{prefix}.{field_name}"
        if path in variables:
            result[field_name] = _format_value(getattr(instance, field_name))

    for field_name, getter in exposure.computed.items():
        path = f"{prefix}.{field_name}"
        if path in variables:
            result[field_name] = _format_value(getter(instance))

    for relation_name, nested_exposure in exposure.relations.items():
        nested_prefix = f"{prefix}.{relation_name}"
        if not any(variable.startswith(f"{nested_prefix}.") for variable in variables):
            continue
        related = getattr(instance, relation_name)
        result[relation_name] = (
            _build_object(
                related,
                nested_exposure,
                nested_prefix,
                variables,
                collection_paths,
                external_values,
            )
            if related is not None
            else None
        )

    for collection_name, collection in exposure.collections.items():
        collection_path = f"{prefix}.{collection_name}"
        if collection_path not in collection_paths:
            continue
        result[collection_name] = _build_collection(
            instance,
            collection,
            collection_path,
            variables,
            collection_paths,
            external_values,
        )

    return result


def _build_collection(
    instance,
    collection,
    collection_path,
    variables,
    collection_paths,
    external_values,
):
    if collection_path in external_values:
        values = external_values.get(collection_path, ())
    elif collection.source_name is None:
        values = ()
    else:
        related_manager = getattr(instance, collection.source_name)
        if not hasattr(related_manager, "all"):
            raise ValidationError(
                f"La relation « {collection_path} » ne fournit pas une collection."
            )
        values = related_manager.all()

    try:
        items = list(values)
    except TypeError as error:
        raise ValidationError(
            f"La collection « {collection_path} » n’est pas itérable."
        ) from error

    item_prefix = collection.item_name
    for item in items:
        if not isinstance(item, collection.exposure.model):
            raise ValidationError(
                f"Un élément de « {collection_path} » ne correspond pas au modèle "
                f"{collection.exposure.model._meta.label}."
            )
    return [
        _build_object(
            item,
            collection.exposure,
            item_prefix,
            variables,
            collection_paths,
            external_values,
        )
        for item in items
    ]


def _format_value(value):
    if value is None:
        return ""
    if isinstance(value, datetime):
        if timezone.is_aware(value):
            value = timezone.localtime(value)
        return value.strftime("%d/%m/%Y %H:%M")
    if isinstance(value, date):
        return value.strftime("%d/%m/%Y")
    if isinstance(value, Decimal):
        return format(value, "f")
    if isinstance(value, (str, int, float, bool)):
        return str(value)
    raise ValidationError(
        f"Le type de valeur « {type(value).__name__} » ne peut pas être rendu."
    )
