from dataclasses import dataclass

from django.core.exceptions import ValidationError

from .discovery import ModelCatalog
from .markers import inspect_docx
from .structure import parse_definition


@dataclass(frozen=True)
class ValidatedDocument:
    definition: object
    scan: object


def validate_template(content, structure, catalog):
    definition = parse_definition(structure)
    if not isinstance(catalog, ModelCatalog):
        raise ValidationError("Un catalogue de données découvert est requis.")
    if catalog.root_model != definition.root_model:
        raise ValidationError(
            "Le modèle racine de la configuration ne correspond pas au catalogue."
        )
    if catalog.root_name != definition.root_name:
        raise ValidationError(
            "Le nom racine de la configuration ne correspond pas au catalogue."
        )

    scan = inspect_docx(content)
    for variable in definition.variables:
        if variable not in catalog.variables:
            raise ValidationError(
                f"La variable « {variable} » n’est pas exposée par le catalogue."
            )

    item_name_to_collection = {}
    for collection_path, collection in catalog.collections.items():
        item_name = collection["item_name"]
        previous_collection = item_name_to_collection.setdefault(
            item_name,
            collection_path,
        )
        if previous_collection != collection_path:
            raise ValidationError(
                f"item_name « {item_name} » ne peut pas désigner plusieurs "
                "collections."
            )

    row_by_collection_variable = {}
    if definition.zones:
        zone_by_pair = {}
        collection_by_item_name = {}
        for zone in definition.zones:
            collection = catalog.collections.get(zone.collection)
            if collection is None:
                raise ValidationError(
                    f"La collection « {zone.collection} » n’existe pas."
                )
            if collection["item_name"] != zone.item_name:
                raise ValidationError(
                    f"La zone « {zone.name} » doit utiliser item_name "
                    f"« {collection['item_name']} » pour « {zone.collection} »."
                )
            previous_collection = collection_by_item_name.setdefault(
                zone.item_name,
                zone.collection,
            )
            if previous_collection != zone.collection:
                raise ValidationError(
                    f"item_name « {zone.item_name} » ne peut pas désigner plusieurs "
                    "collections."
                )
            zone_by_pair[zone.marker_pair] = zone

        if len(scan.marker_pairs) != len(definition.zones):
            raise ValidationError(
                "Le nombre de paires {{ debut }}/{{ fin }} doit correspondre "
                "au nombre de zones configurées."
            )

        configured_rows = set()
        for pair in scan.marker_pairs:
            zone = zone_by_pair.get(pair.index)
            if zone is None:
                raise ValidationError(
                    f"La paire de marqueurs {pair.index} n’est associée à aucune zone."
                )
            if (
                pair.start.row is None
                or pair.end.row is None
                or pair.start.row is not pair.end.row
                or pair.start.table is not pair.end.table
            ):
                raise ValidationError(
                    f"La zone « {zone.name} » doit placer {{ debut }} et {{ fin }} "
                    "dans la même ligne de tableau."
                )
            if pair.start.row in configured_rows:
                raise ValidationError(
                    "Plusieurs zones ne peuvent pas partager la même ligne de tableau."
                )
            configured_rows.add(pair.start.row)

            row_occurrences = [
                occurrence
                for occurrence in scan.variables
                if _row_is_within(occurrence.row, pair.start.row)
            ]
            if not row_occurrences:
                raise ValidationError(
                    f"La ligne répétable de la zone « {zone.name} » ne contient "
                    "aucune variable."
                )
            if not any(
                occurrence.name.startswith(f"{zone.item_name}.")
                for occurrence in row_occurrences
            ):
                raise ValidationError(
                    f"La ligne répétable de la zone « {zone.name} » doit contenir "
                    f"au moins une variable « {zone.item_name}.* »."
                )
            for occurrence in row_occurrences:
                if occurrence.name.startswith(f"{zone.item_name}."):
                    row_by_collection_variable.setdefault(
                        occurrence.name,
                        set(),
                    ).add(zone.name)
    elif len(scan.marker_pairs) > 1:
        raise ValidationError(
            "Un document dynamique ne peut contenir qu’une seule paire "
            "{{ debut }}/{{ fin }}."
        )

    configured_variables = set(definition.variables)
    for occurrence in scan.variables:
        if definition.variables and occurrence.name not in configured_variables:
            raise ValidationError(
                f"La variable « {occurrence.name} » n’est pas déclarée "
                "dans la configuration."
            )
        if occurrence.name not in catalog.variables:
            raise ValidationError(
                f"La variable « {occurrence.name} » n’est pas exposée "
                "par le catalogue."
            )

        matching_collections = [
            (item_name, collection_path)
            for item_name, collection_path in item_name_to_collection.items()
            if occurrence.name.startswith(f"{item_name}.")
        ]
        is_collection_variable = bool(matching_collections)
        matching_zones = [
            zone
            for zone in definition.zones
            if occurrence.name.startswith(f"{zone.item_name}.")
        ]
        if definition.zones and is_collection_variable and not matching_zones:
            raise ValidationError(
                f"La variable de collection « {occurrence.name} » est utilisée "
                "hors d’une zone répétitive configurée."
            )
        if definition.zones and matching_zones and not any(
            zone.name in row_by_collection_variable.get(occurrence.name, set())
            and occurrence.row is not None
            and any(
                pair.index == zone.marker_pair
                and _row_is_within(occurrence.row, pair.start.row)
                for pair in scan.marker_pairs
            )
            for zone in matching_zones
        ):
            raise ValidationError(
                f"La variable de collection « {occurrence.name} » est utilisée "
                "hors de sa ligne répétitive."
            )

    if definition.variables:
        found_variables = {occurrence.name for occurrence in scan.variables}
        for variable in definition.variables:
            if variable in found_variables:
                continue
            raise ValidationError(
                f"La variable configurée « {variable} » n’apparaît pas dans le DOCX."
            )

    return ValidatedDocument(definition, scan)


def _row_is_within(row, target_row):
    current = row
    while current is not None:
        if current is target_row:
            return True
        current = current.getparent()
        while current is not None and not current.tag.endswith("}tr"):
            current = current.getparent()
    return False
