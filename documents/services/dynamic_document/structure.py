import re
from dataclasses import dataclass

from django.core.exceptions import ValidationError


_IDENTIFIER = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")
_MODEL_LABEL = re.compile(r"^[a-zA-Z_][A-Za-z0-9_]*\.[A-Za-z_][A-Za-z0-9_]*$")
_PATH = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*(?:\.[A-Za-z_][A-Za-z0-9_]*)*$")
CONFIG_VERSION = 1


@dataclass(frozen=True)
class ZoneDefinition:
    name: str
    zone_type: str
    collection: str
    item_name: str
    marker_pair: int


@dataclass(frozen=True)
class DocumentDefinition:
    document_type: str
    root_model: str
    root_name: str
    variables: tuple[str, ...]
    zones: tuple[ZoneDefinition, ...]
    version: int = CONFIG_VERSION


def parse_definition(value):
    if isinstance(value, DocumentDefinition):
        value = {
            "version": value.version,
            "document_type": value.document_type,
            "root_model": value.root_model,
            "root_name": value.root_name,
            "variables": list(value.variables),
            "zones": [
                {
                    "name": zone.name,
                    "type": zone.zone_type,
                    "collection": zone.collection,
                    "item_name": zone.item_name,
                    "marker_pair": zone.marker_pair,
                }
                for zone in value.zones
            ],
        }
    if not isinstance(value, dict):
        raise ValidationError("La configuration documentaire doit être un objet JSON.")

    expected_keys = {
        "version",
        "document_type",
        "root_model",
        "root_name",
        "variables",
        "zones",
    }
    unknown_keys = set(value) - expected_keys
    if unknown_keys:
        raise ValidationError(
            f"Clés de configuration inconnues : {', '.join(sorted(unknown_keys))}."
        )

    version = value.get("version")
    if isinstance(version, bool) or version != CONFIG_VERSION:
        raise ValidationError(
            f"La version de configuration doit être {CONFIG_VERSION}."
        )

    document_type = value.get("document_type")
    if not isinstance(document_type, str) or not _IDENTIFIER.fullmatch(document_type):
        raise ValidationError(
            "Le type de document doit être un identifiant simple valide."
        )

    root_model = value.get("root_model")
    if not isinstance(root_model, str) or not _MODEL_LABEL.fullmatch(root_model):
        raise ValidationError(
            "root_model doit utiliser le format « application.Modèle »."
        )

    root_name = value.get("root_name")
    if not isinstance(root_name, str) or not _IDENTIFIER.fullmatch(root_name):
        raise ValidationError("root_name doit être un identifiant simple valide.")

    variables = value.get("variables", [])
    if not isinstance(variables, list) or any(
        not isinstance(variable, str) or not _PATH.fullmatch(variable)
        for variable in variables
    ):
        raise ValidationError(
            "variables doit être une liste de chemins de variables valides."
        )
    if len(set(variables)) != len(variables):
        raise ValidationError("Une variable ne peut être déclarée qu’une seule fois.")

    raw_zones = value.get("zones", [])
    if not isinstance(raw_zones, list):
        raise ValidationError("zones doit être une liste.")

    zones = []
    zone_names = set()
    marker_pairs = set()
    for index, raw_zone in enumerate(raw_zones, start=1):
        if not isinstance(raw_zone, dict):
            raise ValidationError(f"La zone numéro {index} doit être un objet JSON.")
        expected_zone_keys = {
            "name",
            "type",
            "collection",
            "item_name",
            "marker_pair",
        }
        unknown_zone_keys = set(raw_zone) - expected_zone_keys
        if unknown_zone_keys:
            raise ValidationError(
                f"Clés inconnues dans la zone numéro {index} : "
                f"{', '.join(sorted(unknown_zone_keys))}."
            )

        name = raw_zone.get("name")
        if not isinstance(name, str) or not _IDENTIFIER.fullmatch(name):
            raise ValidationError(
                f"Le nom de la zone numéro {index} est invalide."
            )
        if name in zone_names:
            raise ValidationError(f"La zone « {name} » est déclarée plusieurs fois.")
        zone_names.add(name)

        zone_type = raw_zone.get("type")
        if zone_type != "repeat_row":
            raise ValidationError(
                f"Le type de zone « {zone_type} » n’est pas pris en charge."
            )

        collection = raw_zone.get("collection")
        if not isinstance(collection, str) or not _PATH.fullmatch(collection):
            raise ValidationError(
                f"La collection de la zone « {name} » est invalide."
            )

        item_name = raw_zone.get("item_name")
        if not isinstance(item_name, str) or not _IDENTIFIER.fullmatch(item_name):
            raise ValidationError(
                f"item_name de la zone « {name} » est invalide."
            )
        if item_name == root_name:
            raise ValidationError(
                f"item_name de la zone « {name} » ne peut pas remplacer "
                "le nom racine du document."
            )

        marker_pair = raw_zone.get("marker_pair")
        if (
            not isinstance(marker_pair, int)
            or isinstance(marker_pair, bool)
            or marker_pair < 1
        ):
            raise ValidationError(
                f"marker_pair de la zone « {name} » doit être un entier positif."
            )
        if marker_pair in marker_pairs:
            raise ValidationError(
                f"La paire de marqueurs {marker_pair} est associée à plusieurs zones."
            )
        marker_pairs.add(marker_pair)
        zones.append(
            ZoneDefinition(name, zone_type, collection, item_name, marker_pair)
        )

    if marker_pairs and marker_pairs != set(range(1, len(marker_pairs) + 1)):
        raise ValidationError(
            "Les paires de marqueurs doivent être numérotées sans interruption à partir de 1."
        )

    return DocumentDefinition(
        document_type=document_type,
        root_model=root_model,
        root_name=root_name,
        variables=tuple(variables),
        zones=tuple(zones),
        version=version,
    )
