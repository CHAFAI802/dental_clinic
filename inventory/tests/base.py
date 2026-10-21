"""
Helpers partagés par les tests de l'application inventory.

Ces fabriques ne font qu'appeler le code de production tel qu'il est
écrit dans le dépôt : aucune règle métier n'est réimplémentée ici.

Les codes de famille sont générés automatiquement pour rester uniques
(contrainte d'unicité sur InventoryFamily.code) ; une catégorie par
code est réutilisée d'un appel à l'autre (contrainte d'unicité sur
InventoryCategory.code, et les familles exigent une catégorie MAT/CON).
"""
import itertools
from decimal import Decimal

from inventory.models import (
    InventoryCategory,
    InventoryFamily,
    InventoryItem,
    StockEntry,
)

_family_counter = itertools.count(1)


def to_decimal(value):
    return Decimal(str(value))


def create_category(code="CON", name="Consommable", **kwargs):
    existing = InventoryCategory.objects.filter(code=code).first()

    if existing is not None:
        return existing

    return InventoryCategory.objects.create(
        code=code,
        name=name,
        **kwargs,
    )


def create_family(category=None, code=None, name="Famille", **kwargs):
    if category is None:
        category = create_category()

    if code is None:
        code = f"FAM{next(_family_counter):03d}"

    return InventoryFamily.objects.create(
        category=category,
        name=name,
        code=code,
        **kwargs,
    )


def create_item(family=None, name="Produit test", **kwargs):
    if family is None:
        family = create_family()

    return InventoryItem.objects.create(
        name=name,
        family=family,
        **kwargs,
    )


def build_entry(item, quantity, unit_cost="2.00", total_cost=None, **kwargs):
    """Construit une StockEntry sans l'appliquer.

    `total_cost` est calculé par défaut comme le ferait
    StockEntry.apply() (quantité x coût unitaire).
    """
    quantity_dec = to_decimal(quantity)
    unit_cost_dec = to_decimal(unit_cost)

    if total_cost is None:
        total_cost = quantity_dec * unit_cost_dec

    return StockEntry(
        item=item,
        quantity=quantity_dec,
        unit_cost=unit_cost_dec,
        total_cost=to_decimal(total_cost),
        **kwargs,
    )


def create_entry(item, quantity, unit_cost="2.00", apply=True, **kwargs):
    """Construit une StockEntry et, par défaut, l'applique."""
    entry = build_entry(item, quantity, unit_cost, **kwargs)

    if apply:
        entry.apply()

    return entry
