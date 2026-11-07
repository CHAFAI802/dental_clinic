from dataclasses import dataclass, field
from typing import Callable, Mapping

from django.core.exceptions import FieldDoesNotExist, ValidationError
from django.db import models


@dataclass(frozen=True)
class CollectionExposure:
    item_name: str
    exposure: "ModelExposure"
    source_name: str | None = None


@dataclass(frozen=True)
class ModelExposure:
    model: type[models.Model]
    fields: tuple[str, ...] = ()
    relations: Mapping[str, "ModelExposure"] = field(default_factory=dict)
    collections: Mapping[str, CollectionExposure] = field(default_factory=dict)
    computed: Mapping[str, Callable] = field(default_factory=dict)


@dataclass(frozen=True)
class ModelCatalog:
    root_model: str
    root_name: str
    variables: Mapping[str, dict]
    collections: Mapping[str, dict]

    def as_dict(self):
        return {
            "root_model": self.root_model,
            "root_name": self.root_name,
            "variables": dict(self.variables),
            "collections": dict(self.collections),
        }


def discover_model_catalog(exposure, root_name):
    if not isinstance(root_name, str) or not root_name.isidentifier():
        raise ValidationError("Le nom racine du catalogue est invalide.")
    if not isinstance(exposure, ModelExposure):
        raise ValidationError("Une exposition explicite de modèle Django est requise.")
    variables = {}
    collections = {}
    _discover(exposure, root_name, variables, collections, set())
    return ModelCatalog(
        root_model=exposure.model._meta.label,
        root_name=root_name,
        variables=variables,
        collections=collections,
    )


def _discover(exposure, prefix, variables, collections, ancestors):
    if (
        not isinstance(exposure.model, type)
        or not issubclass(exposure.model, models.Model)
    ):
        raise ValidationError("Une exposition doit référencer un modèle Django.")

    model_key = exposure.model._meta.label_lower
    if model_key in ancestors:
        raise ValidationError(
            f"Relation cyclique non prise en charge dans l’exposition {model_key}."
        )
    ancestors = ancestors | {model_key}

    for field_name in exposure.fields:
        field = _concrete_field(exposure.model, field_name)
        if field.is_relation:
            raise ValidationError(
                f"Le champ relationnel {model_key}.{field_name} doit être déclaré "
                "dans relations ou collections."
            )
        path = f"{prefix}.{field_name}"
        if path in variables:
            raise ValidationError(f"L’exposition de « {path} » est dupliquée.")
        variables[path] = {
            "model": exposure.model._meta.label,
            "field": field_name,
            "label": str(field.verbose_name),
            "type": field.get_internal_type(),
            "kind": "field",
            "description": str(field.help_text),
        }

    for field_name, getter in exposure.computed.items():
        if not callable(getter):
            raise ValidationError(
                f"La valeur calculée {model_key}.{field_name} doit être autorisée "
                "par un callable explicite."
            )
        path = f"{prefix}.{field_name}"
        if path in variables:
            raise ValidationError(f"L’exposition de « {path} » est dupliquée.")
        variables[path] = {
            "model": exposure.model._meta.label,
            "field": field_name,
            "label": field_name.replace("_", " "),
            "type": "computed",
            "kind": "computed",
            "description": "",
        }

    for relation_name, nested_exposure in exposure.relations.items():
        relation = _concrete_field(exposure.model, relation_name)
        if not relation.is_relation or not (
            relation.many_to_one or relation.one_to_one
        ):
            raise ValidationError(
                f"{model_key}.{relation_name} n’est pas une relation ForeignKey "
                "ou OneToOneField."
            )
        if relation.remote_field.model is not nested_exposure.model:
            raise ValidationError(
                f"L’exposition de {model_key}.{relation_name} ne correspond pas "
                "au modèle lié."
            )
        _discover(
            nested_exposure,
            f"{prefix}.{relation_name}",
            variables,
            collections,
            ancestors,
        )

    for collection_name, collection in exposure.collections.items():
        if not isinstance(collection, CollectionExposure):
            raise ValidationError(
                f"La collection {model_key}.{collection_name} est mal configurée."
            )
        if not collection.item_name.isidentifier():
            raise ValidationError(
                f"Le nom d’élément de {model_key}.{collection_name} est invalide."
            )
        if collection.source_name is not None:
            relation = _concrete_field(exposure.model, collection.source_name)
            if not relation.is_relation or not (
                relation.one_to_many or relation.many_to_many
            ):
                raise ValidationError(
                    f"{model_key}.{collection.source_name} n’est pas une relation "
                    "de collection."
                )
            if relation.related_model is not collection.exposure.model:
                raise ValidationError(
                    f"L’exposition de la collection {model_key}.{collection_name} "
                    "ne correspond pas au modèle lié."
                )

        collection_path = f"{prefix}.{collection_name}"
        collections[collection_path] = {
            "model": collection.exposure.model._meta.label,
            "item_name": collection.item_name,
            "source": collection.source_name or "external",
            "kind": "collection",
        }
        _discover(
            collection.exposure,
            collection.item_name,
            variables,
            collections,
            ancestors,
        )


def _concrete_field(model, field_name):
    try:
        field = model._meta.get_field(field_name)
    except FieldDoesNotExist as error:
        raise ValidationError(
            f"Le champ « {model._meta.label}.{field_name} » n’existe pas."
        ) from error
    if field.auto_created and not field.concrete:
        return field
    if not field.concrete:
        raise ValidationError(
            f"Le champ « {model._meta.label}.{field_name} » n’est pas exposable."
        )
    return field


def get_builtin_exposures():
    from accounts.models import User
    from billing.models import Invoice, InvoiceLine, Payment, PaymentMethod
    from inventory.models import InventoryFamily, InventoryItem, Unit
    from patients.models import Medication, Patient
    from prescriptions.models import Prescription

    patient = ModelExposure(
        model=Patient,
        fields=(
            "first_name",
            "middle_name",
            "last_name",
            "birthdate",
            "patient_code",
            "phone",
            "address",
            "city",
        ),
    )
    dentist = ModelExposure(
        model=User,
        fields=("first_name", "last_name", "email", "phone"),
    )
    medication = ModelExposure(
        model=Medication,
        fields=(
            "name",
            "dosage",
            "frequency",
            "route",
            "start_date",
            "end_date",
            "notes",
        ),
    )
    prescription = ModelExposure(
        model=Prescription,
        fields=("generated_at", "status", "notes"),
        relations={"patient": patient, "dentist": dentist},
        collections={
            "medications": CollectionExposure(
                item_name="medication",
                exposure=medication,
            )
        },
    )

    invoice_line = ModelExposure(
        model=InvoiceLine,
        fields=("description", "quantity", "unit_price", "tax_rate"),
        computed={
            "subtotal": lambda line: line.subtotal,
            "tax_amount": lambda line: line.tax_amount,
            "total": lambda line: line.total,
        },
    )
    invoice = ModelExposure(
        model=Invoice,
        fields=(
            "reference_number",
            "issued_at",
            "due_date",
            "status",
            "subtotal",
            "tax_amount",
            "total_amount",
            "paid_amount",
            "balance_due",
            "notes",
        ),
        relations={"patient": patient},
        collections={
            "lines": CollectionExposure("line", invoice_line, "lines")
        },
    )
    payment_method = ModelExposure(model=PaymentMethod, fields=("name", "provider"))
    payment = ModelExposure(
        model=Payment,
        fields=("payment_at", "amount", "reference", "status"),
        relations={
            "invoice": invoice,
            "patient": patient,
            "method": payment_method,
        },
    )
    inventory_item = ModelExposure(
        model=InventoryItem,
        fields=(
            "sku",
            "name",
            "description",
            "reorder_point",
            "reorder_quantity",
            "stock_quantity",
            "is_perishable",
            "is_active",
        ),
        relations={
            "unit": ModelExposure(
                model=Unit,
                fields=("name", "symbol"),
            )
        },
    )
    inventory_family = ModelExposure(
        model=InventoryFamily,
        fields=("name", "code"),
        collections={
            "items": CollectionExposure(
                item_name="item",
                exposure=inventory_item,
                source_name="items",
            )
        },
    )
    return {
        exposure.model._meta.label: exposure
        for exposure in (prescription, invoice, payment, inventory_family)
    }


def get_builtin_catalog(model_label, root_name):
    exposure = get_builtin_exposures().get(model_label)
    if exposure is None:
        raise ValidationError(
            f"Le modèle « {model_label} » n’est pas autorisé pour les documents dynamiques."
        )
    return discover_model_catalog(exposure, root_name)


def get_builtin_catalogs():
    catalog_details = (
        (
            "prescription",
            "prescriptions.Prescription",
            "Ordonnance",
            "Catalogue documentaire uniquement; le workflow d’ordonnance existant reste inchangé.",
            False,
        ),
        (
            "invoice",
            "billing.Invoice",
            "Facture",
            "Facture, patient, montants calculés et lignes de facture.",
            True,
        ),
        (
            "payment",
            "billing.Payment",
            "Reçu de paiement",
            "Paiement réel, facture associée, patient et méthode de paiement.",
            True,
        ),
        (
            "inventory",
            "inventory.InventoryFamily",
            "Suivi de stock",
            "Famille sélectionnée et articles avec leurs quantités actuelles.",
            True,
        ),
    )
    exposures = get_builtin_exposures()
    catalogs = []
    for root_name, model_label, label, description, generation_enabled in catalog_details:
        catalog = discover_model_catalog(exposures[model_label], root_name).as_dict()
        catalog.update(
            {
                "document_type": root_name,
                "label": label,
                "description": description,
                "generation_enabled": generation_enabled,
            }
        )
        catalogs.append(catalog)
    return catalogs


def queryset_hints(exposure):
    select_related = []
    prefetch_related = []
    _collect_query_hints(exposure, "", select_related, prefetch_related)
    return tuple(dict.fromkeys(select_related)), tuple(dict.fromkeys(prefetch_related))


def _collect_query_hints(exposure, prefix, select_related, prefetch_related):
    _collect_query_hints_for_path(
        exposure,
        prefix,
        select_related,
        prefetch_related,
        inside_collection=False,
    )


def _collect_query_hints_for_path(
    exposure,
    prefix,
    select_related,
    prefetch_related,
    *,
    inside_collection,
):
    for name, nested in exposure.relations.items():
        path = f"{prefix}__{name}" if prefix else name
        if inside_collection:
            prefetch_related.append(path)
        else:
            select_related.append(path)
        _collect_query_hints_for_path(
            nested,
            path,
            select_related,
            prefetch_related,
            inside_collection=inside_collection,
        )
    for name, collection in exposure.collections.items():
        if collection.source_name is None:
            continue
        path = f"{prefix}__{collection.source_name}" if prefix else collection.source_name
        prefetch_related.append(path)
        _collect_query_hints_for_path(
            collection.exposure,
            path,
            select_related,
            prefetch_related,
            inside_collection=True,
        )
