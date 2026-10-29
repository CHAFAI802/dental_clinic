from django.db import models, transaction
from django.core.exceptions import ValidationError
from decimal import Decimal, DecimalException
from dental_clinic.common import TimestampedModel
from django.utils import timezone
from datetime import timedelta
import decimal


class InventoryCategory(models.Model):
    class CategoryCode(models.TextChoices):
        MATERIAL = "MAT", "Matériel"
        CONSUMABLE = "CON", "Consommable"

    code = models.CharField(
        max_length=3,
        choices=CategoryCode.choices,
        unique=True,
        null=True,
        blank=True,
    )
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    parent = models.ForeignKey(
        "inventory.InventoryCategory",
        null=True,
        blank=True,
        related_name="children",
        on_delete=models.SET_NULL,
    )

    def __str__(self):
        return self.name

class Supplier(models.Model):
    name = models.CharField(max_length=255)
    contact_name = models.CharField(max_length=255, blank=True)
    phone = models.CharField(max_length=30, blank=True)
    email = models.EmailField(blank=True)
    address = models.TextField(blank=True)
    notes = models.TextField(blank=True)

    def __str__(self):
        return self.name

class InventoryFamily(TimestampedModel):
    category = models.ForeignKey(
        "inventory.InventoryCategory",
        on_delete=models.PROTECT,
        related_name="families",
    )
    name = models.CharField(max_length=255)
    code = models.CharField(
        max_length=6,
        unique=True,
        help_text="Code de famille, par exemple GANT, MASQ ou TURB.",
    )
    is_active = models.BooleanField(default=True)

    # Prochain numéro disponible pour cette famille.
    next_sku_number = models.PositiveBigIntegerField(default=1)

    def clean(self):
        super().clean()

        if self.code:
            self.code = self.code.strip().upper()

            if not self.code.isalnum():
                raise ValidationError({
                    "code": (
                        "Le code doit contenir uniquement des lettres "
                        "et des chiffres."
                    )
                })

        if self.category_id:
            if self.category.code not in InventoryCategory.CategoryCode.values:
                raise ValidationError({
                    "category": (
                        "La famille doit appartenir à une catégorie "
                        "Matériel (MAT) ou Consommable (CON)."
                    )
                })

        # Le code d'une famille utilisée par des produits est immuable.
        if self.pk:
            previous = InventoryFamily.objects.filter(pk=self.pk).first()

            if previous and previous.code != self.code:
                if previous.items.exists():
                    raise ValidationError({
                        "code": (
                            "Le code ne peut pas être modifié après "
                            "la création de produits associés."
                        )
                    })

    def save(self, *args, **kwargs):
        self.full_clean()
        return super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.category.code}-{self.code} — {self.name}"

class Unit(models.Model):
    name = models.CharField(
        max_length=100,
        unique=True,
        verbose_name="Nom de l'unité",
    )
    symbol = models.CharField(
        max_length=20,
        unique=True,
        verbose_name="Symbole",
    )

    is_active = models.BooleanField(
        default=True,
        verbose_name="Active",
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Date de création",
    )

    class Meta:
        verbose_name = "Unité"
        verbose_name_plural = "Unités"
        ordering = ["name"]

    def __str__(self):
        return f"{self.name} ({self.symbol})"

class InventoryItem(TimestampedModel):
    sku = models.CharField(
        max_length=64,
        unique=True,
        editable=False,
        blank=True,
    )
    name = models.CharField(max_length=255)

    # Relation utilisée pour générer le SKU.
    family = models.ForeignKey(
        "inventory.InventoryFamily",
        null=True,
        blank=True,
        on_delete=models.PROTECT,
        related_name="items",
    )

    description = models.TextField(blank=True)
    unit = models.ForeignKey(
        "inventory.Unit",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
    )
    reorder_point = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,)
    expiration_alert_days = models.PositiveIntegerField(
        default=30,
        help_text=(
            "Nombre de jours avant la péremption à partir duquel "
            "une alerte doit être déclenchée."
        ),
    )
    reorder_quantity = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
    )
    stock_quantity = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0,
    )

    is_perishable = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)

    def clean(self):
        super().clean()

        if (
            self.stock_quantity is not None
            and self.stock_quantity < 0
        ):
            raise ValidationError({
                "stock_quantity": (
                    "Stock quantity must be greater than or equal to zero."
                )
            })

    def save(self, *args, **kwargs):
        # Un produit existant conserve son SKU.
        if self.pk:
            previous = InventoryItem.objects.get(pk=self.pk)

            if self.sku != previous.sku:
                raise ValidationError({
                    "sku": "Le SKU d'un produit existant ne peut pas être modifié."
                })

            if self.family_id != previous.family_id:
                raise ValidationError({
                    "family": (
                        "La famille ne peut pas être modifiée après "
                        "la création du produit."
                    )
                })

            self.full_clean()
            return super().save(*args, **kwargs)

        # Un nouveau produit doit appartenir à une famille.
        if not self.family_id:
            raise ValidationError({
                "family": (
                    "Une famille doit être sélectionnée pour générer le SKU."
                )
            })

        # Le verrouillage empêche deux créations simultanées
        # d'utiliser le même numéro pour une même famille.
        with transaction.atomic():
            family = (
                InventoryFamily.objects
                .select_for_update()
                .select_related("category")
                .get(pk=self.family_id)
            )

            if not family.is_active:
                raise ValidationError({
                    "family": (
                        "Impossible de créer un produit dans une "
                        "famille inactive."
                    )
                })

            category_code = family.category.code

            if category_code not in InventoryCategory.CategoryCode.values:
                raise ValidationError({
                    "family": (
                        "La catégorie de la famille doit être MAT ou CON."
                    )
                })

            number = family.next_sku_number

            self.sku = (
                f"DCL-{category_code}-{family.code}-{number:06d}"
            )

            family.next_sku_number = number + 1
            family.save(update_fields=["next_sku_number"])

            # Valide les champs et le produit avant son enregistrement.
            self.full_clean()

            return super().save(*args, **kwargs)

    class Meta:
        constraints = [
            models.CheckConstraint(
                condition=models.Q(stock_quantity__gte=0),
                name="inventory_stock_quantity_non_negative",
            ),
        ]

    def __str__(self):
        return self.name

class StockEntry(TimestampedModel):
    item = models.ForeignKey(
        "inventory.InventoryItem",
        related_name="entries",
        on_delete=models.CASCADE,
    )
    supplier = models.ForeignKey(
        "inventory.Supplier",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
    )
    quantity = models.DecimalField(
        max_digits=12,
        decimal_places=2,
    )
    remaining_quantity = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0,
        editable=False,
    )
    unit_cost = models.DecimalField(
        max_digits=12,
        decimal_places=2,
    )
    total_cost = models.DecimalField(
        max_digits=14,
        decimal_places=2,
    )
    received_at = models.DateTimeField(
        default=timezone.now,
    )
    batch_number = models.CharField(
        max_length=128,
        blank=True,
    )
    expiration_date = models.DateField(
        null=True,
        blank=True,
    )
    received_by = models.ForeignKey(
        "accounts.User",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
    )
    comments = models.TextField(blank=True)

    def clean(self):
        super().clean()

        errors = {}

        if self.quantity is not None and self.quantity <= 0:
            errors["quantity"] = (
                "La quantité reçue doit être strictement positive."
            )

        if self.unit_cost is not None and self.unit_cost < 0:
            errors["unit_cost"] = (
                "Le coût unitaire ne peut pas être négatif."
            )

        if (
            self.quantity is not None
            and self.unit_cost is not None
            and self.total_cost is not None
            and self.total_cost != self.quantity * self.unit_cost
        ):
            errors["total_cost"] = (
                "Le coût total doit correspondre à la quantité "
                "multipliée par le coût unitaire."
            )

        if self.item_id:
            if self.item.is_perishable and not self.expiration_date:
                errors["expiration_date"] = (
                    "La date de péremption est obligatoire pour "
                    "un produit périssable."
                )

            if not self.item.is_perishable and self.expiration_date:
                errors["expiration_date"] = (
                    "Une date de péremption ne peut pas être renseignée "
                    "pour un produit déclaré non périssable."
                )

        if errors:
            raise ValidationError(errors)

    def save(self, *args, **kwargs):
        if self.pk is None:
            # Une nouvelle entrée doit passer par apply().
            if not getattr(self, "_applying", False):
                raise ValidationError(
                    "Une entrée doit être enregistrée par la méthode apply()."
                )
        else:
            # Une entrée existante ne peut être modifiée que pour
            # actualiser sa quantité restante lors d'un mouvement de stock.
            if not getattr(self, "_updating_stock", False):
                raise ValidationError(
                    "Une entrée enregistrée ne peut pas être modifiée "
                    "directement."
                )

        return super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        raise ValidationError(
            "Une entrée de stock enregistrée ne peut pas être supprimée."
        )

    @transaction.atomic
    def apply(self):
        # Empêcher une seconde application.
        if self.pk is not None:
            raise ValidationError(
                "Cette entrée existe déjà. Elle ne peut pas être "
                "appliquée une seconde fois."
            )

        # Vérifier qu'un produit est sélectionné.
        if not self.item_id:
            raise ValidationError(
                "Un produit doit être sélectionné."
            )

        # Verrouiller le produit pendant la mise à jour du stock.
        item = (
            InventoryItem.objects
            .select_for_update()
            .get(pk=self.item_id)
        )

        # calculer le coût total coté serveur pour éviter les incohérences.
        self.total_cost = (self.quantity * self.unit_cost).quantize(decimal.Decimal("0.01"))

        # Valider les données avant toute modification.
        self.full_clean()

        # Initialiser la quantité restante du nouveau lot.
        self.remaining_quantity = self.quantity

        # Autoriser temporairement l'enregistrement contrôlé.
        self._applying = True
        try:
            self.save()
        finally:
            self._applying = False

        # Mettre à jour le stock physique global.
        item.stock_quantity += self.quantity

        item.save(
            update_fields=[
                "stock_quantity",
                "updated_at",
            ]
        )

        StockAlert.sync_for_item(item.pk)
        return item.stock_quantity

    def __str__(self):
        return (
            f"Entrée {self.pk} — "
            f"{self.item.name} — {self.quantity}"
        )

class StockExit(TimestampedModel):
    class SelectionMode(models.TextChoices):
        AUTOMATIC = "automatic", "Automatique"
        MANUAL = "manual", "Manuel"

    item = models.ForeignKey(
        "inventory.InventoryItem",
        related_name="exits",
        on_delete=models.CASCADE,
    )
    treatment = models.ForeignKey(
        "treatments.Treatment",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
    )
    quantity = models.DecimalField(
        max_digits=12,
        decimal_places=2,
    )
    exited_at = models.DateTimeField(
        default=timezone.now,
    )
    used_by = models.ForeignKey(
        "accounts.User",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
    )
    usage_type = models.CharField(max_length=64)
    comments = models.TextField(blank=True)

    # Sélection explicite de lots pour le mode MANUAL.
    # Contrat : liste de {"stock_entry": <pk>, "quantity": <Decimal>}.
    # Le backend n'accepte ce champ que pour selection_mode = MANUAL
    # et ne le déduit que si la validation est réussie.
    manual_allocations = models.JSONField(
        default=list,
        blank=True,
        null=True,
        help_text='Lots sélectionnés en mode MANUAL : [{"stock_entry": <pk>, "quantity": <Decimal>}].',
    )

    selection_mode = models.CharField(
        max_length=10,
        choices=SelectionMode.choices,
        default=SelectionMode.AUTOMATIC,
    )

    def clean(self):
        super().clean()

        errors = {}

        if self.quantity is not None and self.quantity <= 0:
            errors["quantity"] = (
                "La quantité sortie doit être strictement positive."
            )

        if self.item_id and not self.item.is_active:
            errors["item"] = (
                "Impossible de sortir le stock d'un produit inactif."
            )

        if self.selection_mode not in self.SelectionMode.values:
            errors["selection_mode"] = (
                "Le mode de sélection est invalide."
            )

        if self.selection_mode == self.SelectionMode.MANUAL:
            if not isinstance(self.manual_allocations, list):
                errors["manual_allocations"] = [
                    "Le format des allocations manuelles n'est pas valide."
                ]
            elif not self.manual_allocations:
                errors["manual_allocations"] = [
                    "Le mode manuel exige au moins un lot."
                ]
            else:
                total_allocated = Decimal("0")
                seen_entries = set()
                latest_error = None

                for idx, allocation in enumerate(self.manual_allocations):
                    if not isinstance(allocation, dict):
                        errors["manual_allocations"] = [
                            f"L'allocation #{idx + 1} n'est pas un objet."
                        ]
                        latest_error = "manual_allocations"
                        continue

                    stock_entry = allocation.get("stock_entry")
                    quantity = allocation.get("quantity")

                    if stock_entry is None:
                        errors.setdefault("manual_allocations", []).append(
                            f"L'allocation #{idx + 1} ne désigne pas de lot."
                        )
                        latest_error = "manual_allocations"

                    if quantity is None:
                        errors.setdefault("manual_allocations", []).append(
                            f"L'allocation #{idx + 1} ne précise pas de quantité."
                        )
                        latest_error = "manual_allocations"

                    if stock_entry is not None and quantity is not None:
                        try:
                            quantity = Decimal(str(quantity))
                        except Exception:
                            errors.setdefault("manual_allocations", []).append(
                                f"L'allocation #{idx + 1} a une quantité invalide."
                            )
                            latest_error = "manual_allocations"
                            continue

                        if quantity <= 0:
                            errors.setdefault("manual_allocations", []).append(
                                f"L'allocation #{idx + 1} doit être strictement positive."
                            )
                            latest_error = "manual_allocations"

                        if stock_entry in seen_entries:
                            errors.setdefault("manual_allocations", []).append(
                                f"L'allocation #{idx + 1} désigne un lot déjà utilisé."
                            )
                            latest_error = "manual_allocations"
                        else:
                            seen_entries.add(stock_entry)

                        total_allocated += quantity

                        if self.item_id is not None:
                            try:
                                lot = StockEntry.objects.get(pk=stock_entry)

                                if lot.item_id != self.item_id:
                                    errors.setdefault("manual_allocations", []).append(
                                        f"L'allocation #{idx + 1} désigne un lot "
                                        f"d'un autre article."
                                    )
                                    latest_error = "manual_allocations"

                                if self.item.is_perishable:
                                    if not lot.expiration_date:
                                        errors.setdefault("manual_allocations", []).append(
                                            f"L'allocation #{idx + 1} désigne un lot "
                                            f"périmé ou sans date de péremption."
                                        )
                                        latest_error = "manual_allocations"
                                    elif lot.expiration_date < timezone.localdate():
                                        errors.setdefault("manual_allocations", []).append(
                                            f"L'allocation #{idx + 1} désigne un lot périmé "
                                            f"({lot.expiration_date})."
                                        )
                                        latest_error = "manual_allocations"

                            except DecimalException:
                                errors.setdefault("manual_allocations", []).append(
                                    f"L'allocation #{idx + 1} a une quantité invalide."
                                )
                                latest_error = "manual_allocations"
                            except StockEntry.DoesNotExist:
                                errors.setdefault("manual_allocations", []).append(
                                    f"L'allocation #{idx + 1} désigne un lot qui n'existe pas."
                                )
                                latest_error = "manual_allocations"

                if total_allocated != self.quantity:
                    errors.setdefault("quantity", []).append(
                        f"La somme des lots sélectionnés ({total_allocated}) "
                        f"doit correspondre à la quantité de sortie ({self.quantity})."
                    )

        if errors:
            raise ValidationError(errors)

    def save(self, *args, **kwargs):
        # Une sortie doit obligatoirement passer par apply().
        if not getattr(self, "_applying", False):
            raise ValidationError(
                "Une sortie doit être enregistrée par la méthode apply()."
            )

        if self.pk is not None:
            raise ValidationError(
                "Une sortie enregistrée ne peut pas être modifiée."
            )

        return super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        raise ValidationError(
            "Une sortie enregistrée ne peut pas être supprimée. "
            "Une procédure d'annulation traçable sera nécessaire."
        )

    @transaction.atomic
    def apply(self):
        if self.pk is not None:
            raise ValidationError(
                "Cette sortie existe déjà et ne peut pas être "
                "appliquée une seconde fois."
            )

        if not self.item_id:
            raise ValidationError(
                "Un produit doit être sélectionné."
            )

        self.full_clean()

        # Verrouiller le produit pour éviter les sorties concurrentes.
        item = (
            InventoryItem.objects
            .select_for_update()
            .get(pk=self.item_id)
        )

        if not item.is_active:
            raise ValidationError(
                "Impossible de sortir le stock d'un produit inactif."
            )

        if self.selection_mode == self.SelectionMode.MANUAL:
            allocations = self._apply_manual(item)
        else:
            allocations = self._apply_automatic(item)

        # Enregistrer la sortie et les lots dans la transaction.
        self._applying = True
        try:
            self.save()
        finally:
            self._applying = False

        for lot, allocated_quantity in allocations:
            lot.remaining_quantity -= allocated_quantity

            lot._updating_stock = True
            try:
                lot.save(
                    update_fields=[
                        "remaining_quantity",
                        "updated_at",
                    ]
                )
            finally:
                lot._updating_stock = False

            StockExitAllocation.objects.create(
                stock_exit=self,
                stock_entry=lot,
                quantity=allocated_quantity,
            )

        # Actualiser le stock physique global.
        item.stock_quantity -= self.quantity

        item.save(
            update_fields=[
                "stock_quantity",
                "updated_at",
            ]
        )

        StockAlert.sync_for_item(item.pk)
        return item.stock_quantity

    def _apply_manual(self, item):
        """Prélèvement manuel : les lots et quantités sont donnés par
        l'utilisateur dans `self.manual_allocations`.

        Règles appliquées :
          - chaque lot appartient à l'article
          - chaque quantité strictement positive
          - la somme des quantités est égale à la quantité de sortie
          - pas de lot au-delà de sa quantité restante
          - un lot périmé est exclu pour un produit périssable
          - les allocations enregistrées reflètent exactement le prélèvement
        """
        if self.manual_allocations is None or not isinstance(self.manual_allocations, list):
            raise ValidationError({
                "manual_allocations": "Le mode manuel attend une liste de lots."
            })

        total = Decimal("0")
        allocations = []
        seen_entries = set()

        for idx, allocation in enumerate(self.manual_allocations):
            stock_entry = allocation.get("stock_entry")
            quantity = allocation.get("quantity")

            if stock_entry is None or quantity is None:
                continue

            try:
                quantity = Decimal(str(quantity))
            except Exception:
                raise ValidationError({
                    "manual_allocations": f"L'allocation #{idx + 1} a une quantité invalide."
                })

            if quantity <= 0:
                raise ValidationError({
                    "manual_allocations": f"L'allocation #{idx + 1} doit être strictement positive."
                })

            if stock_entry in seen_entries:
                raise ValidationError({
                    "manual_allocations": f"L'allocation #{idx + 1} désigne un lot déjà utilisé."
                })
            seen_entries.add(stock_entry)

            try:
                lot = StockEntry.objects.select_for_update().get(pk=stock_entry)
            except StockEntry.DoesNotExist:
                raise ValidationError({
                    "manual_allocations": f"L'allocation #{idx + 1} désigne un lot qui n'existe pas."
                })

            if lot.item_id != item.pk:
                raise ValidationError({
                    "manual_allocations": "Un lot ne peut être prélevé que sur l'article de la sortie."
                })

            if item.is_perishable and lot.expiration_date and lot.expiration_date < timezone.localdate():
                raise ValidationError({
                    "manual_allocations": f"L'allocation #{idx + 1} désigne un lot périmé."
                })

            if lot.remaining_quantity < quantity:
                raise ValidationError({
                    "manual_allocations": f"La quantité demandée sur le lot {lot.pk} "
                                    f"dépasse la quantité restante ({lot.remaining_quantity})."
                })

            # Ne pas modifier le lot ici : apply() applique chaque
            # allocation une seule fois après validation de toutes les données.
            allocations.append((lot, quantity))

        return allocations

    def _apply_automatic(self, item):
        """Prélèvement automatique FIFO (non périssable) ou FEFO
        (périssable), inchangé par rapport au comportement antérieur.
        """
        lots = StockEntry.objects.select_for_update().filter(
            item_id=item.pk,
            remaining_quantity__gt=0,
        )

        if item.is_perishable:
            today = timezone.localdate()
            lots = (
                lots.filter(expiration_date__gte=today)
                .order_by("expiration_date", "received_at", "pk")
            )
        else:
            lots = lots.order_by("received_at", "pk")

        lots = list(lots)

        available_quantity = sum(
            (lot.remaining_quantity for lot in lots),
            start=self.quantity * 0,
        )

        if available_quantity < self.quantity:
            raise ValidationError({
                "quantity": (
                    "Stock utilisable insuffisant pour cette sortie. "
                    f"Quantité demandée : {self.quantity} ; "
                    f"quantité utilisable : {available_quantity}."
                )
            })

        if item.stock_quantity < self.quantity:
            raise ValidationError({
                "quantity": (
                    "La quantité demandée dépasse le stock physique "
                    "enregistré du produit."
                )
            })

        allocations = []
        remaining_to_exit = self.quantity

        for lot in lots:
            if remaining_to_exit <= 0:
                break

            allocated_quantity = min(
                lot.remaining_quantity,
                remaining_to_exit,
            )

            allocations.append((lot, allocated_quantity))
            remaining_to_exit -= allocated_quantity

        if remaining_to_exit > 0:
            raise ValidationError(
                "Les lots disponibles ne permettent pas de satisfaire "
                "la sortie demandée."
            )

        return allocations

    def __str__(self):
        return (
            f"Sortie {self.pk} — "
            f"{self.item.name} — {self.quantity}"
        )

class StockExitAllocation(TimestampedModel):
    stock_exit = models.ForeignKey(
        "inventory.StockExit",
        related_name="exit_allocations",
        on_delete=models.CASCADE,
    )
    stock_entry = models.ForeignKey(
        "inventory.StockEntry",
        related_name="exit_allocations",
        on_delete=models.PROTECT,
    )
    quantity = models.DecimalField(
        max_digits=12,
        decimal_places=2,
    )

    def clean(self):
        super().clean()

        if self.quantity is not None and self.quantity <= 0:
            raise ValidationError({
                "quantity": (
                    "La quantité prélevée doit être strictement positive."
                )
            })

    def __str__(self):
        return (
            f"{self.stock_exit_id} — "
            f"{self.stock_entry.batch_number} — "
            f"{self.quantity}"
        )

class StockAlert(TimestampedModel):
    class AlertType(models.TextChoices):
        LOW_STOCK = "low_stock", "Stock insuffisant"
        EXPIRATION = "expiration", "Péremption"

    stock_entry = models.ForeignKey(
        "inventory.StockEntry",
        related_name="alerts",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
    )

    item = models.ForeignKey(
        "inventory.InventoryItem",
        related_name="alerts",
        on_delete=models.PROTECT,
    )

    alert_type = models.CharField(
        max_length=20,
        choices=AlertType.choices,
    )

    current_quantity = models.DecimalField(
        max_digits=12,
        decimal_places=2,
    )

    created_at = models.DateTimeField(
        default=timezone.now,
        editable=False,
    )

    def clean(self):
        super().clean()

        errors = {}

        if self.current_quantity is not None and self.current_quantity < 0:
            errors["current_quantity"] = (
                "La quantité ne peut pas être négative."
            )

        if self.alert_type == self.AlertType.LOW_STOCK:
            if self.stock_entry_id:
                errors["stock_entry"] = (
                    "Une alerte de stock insuffisant ne doit pas "
                    "être associée à un lot."
                )

            if self.item_id and self.item.reorder_point is None:
                errors["item"] = (
                    "Le seuil de réapprovisionnement doit être défini."
                )

        elif self.alert_type == self.AlertType.EXPIRATION:
            if not self.stock_entry_id:
                errors["stock_entry"] = (
                    "Une alerte de péremption doit identifier un lot."
                )
            elif self.item_id:
                if self.stock_entry.item_id != self.item_id:
                    errors["stock_entry"] = (
                        "Le lot doit appartenir au produit concerné."
                    )

            if self.item_id and not self.item.is_perishable:
                errors["item"] = (
                    "Une alerte de péremption concerne un produit périssable."
                )

        if errors:
            raise ValidationError(errors)

    @classmethod
    @transaction.atomic
    def sync_for_item(cls, item_id):
        """
        Synchronise les alertes courantes d'un produit.

        Ne modifie jamais les quantités en stock.
        """
        item = (
            InventoryItem.objects
            .select_for_update()
            .get(pk=item_id)
        )

        # 1. Alerte de stock insuffisant.
        low_stock_alerts = cls.objects.filter(
            item_id=item.pk,
            alert_type=cls.AlertType.LOW_STOCK,
        )

        if (
            item.reorder_point is not None
            and item.stock_quantity <= item.reorder_point
        ):
            cls.objects.update_or_create(
                item_id=item.pk,
                alert_type=cls.AlertType.LOW_STOCK,
                defaults={
                    "stock_entry": None,
                    "current_quantity": item.stock_quantity,
                },
            )
        else:
            low_stock_alerts.delete()

        # 2. Alertes de péremption.
        expiration_alerts = cls.objects.filter(
            item_id=item.pk,
            alert_type=cls.AlertType.EXPIRATION,
        )

        if not item.is_perishable:
            expiration_alerts.delete()
            return

        date_limite = (
            timezone.localdate()
            + timedelta(days=item.expiration_alert_days)
        )

        # Un lot reste concerné tant qu'il contient du stock et que
        # sa date de péremption est atteinte ou dans la période d'alerte.
        lots_a_alerter = list(
            StockEntry.objects
            .select_for_update()
            .filter(
                item_id=item.pk,
                remaining_quantity__gt=0,
                expiration_date__isnull=False,
                expiration_date__lte=date_limite,
            )
            .order_by("pk")
        )

        lot_ids_a_alerter = []

        for lot in lots_a_alerter:
            lot_ids_a_alerter.append(lot.pk)

            cls.objects.update_or_create(
                stock_entry_id=lot.pk,
                alert_type=cls.AlertType.EXPIRATION,
                defaults={
                    "item_id": item.pk,
                    "current_quantity": lot.remaining_quantity,
                },
            )

        # Supprimer les alertes qui ne correspondent plus à un lot
        # devant être signalé.
        alertes_obsoletes = cls.objects.filter(
            item_id=item.pk,
            alert_type=cls.AlertType.EXPIRATION,
        )

        if lot_ids_a_alerter:
            alertes_obsoletes.exclude(
                stock_entry_id__in=lot_ids_a_alerter,
            ).delete()
        else:
            alertes_obsoletes.delete()


    @classmethod
    def sync_all(cls):
        """
        Vérifie les alertes de tous les produits.

        Cette méthode peut être appelée périodiquement, même en
        l'absence de mouvements de stock.
        """
        item_ids = (
            InventoryItem.objects
            .order_by("pk")
            .values_list("pk", flat=True)
        )

        for item_id in item_ids.iterator():
            cls.sync_for_item(item_id)

    def __str__(self):
        return f"{self.get_alert_type_display()} — {self.item.name}"

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["item"],
                condition=models.Q(alert_type="low_stock"),
                name="unique_low_stock_alert_per_item",
            ),
            models.UniqueConstraint(
                fields=["stock_entry"],
                condition=models.Q(alert_type="expiration"),
                name="unique_expiration_alert_per_entry",
            ),
        ]

class StockDestruction(TimestampedModel):
    class DestructionStatus(models.TextChoices):
        RECORDED = "recorded", "Enregistrée"
        COMPLETED = "completed", "Destruction effectuée"

    destroyed_by = models.ForeignKey(
        "accounts.User",
        null=True,
        blank=True,
        related_name="stock_destructions",
        on_delete=models.SET_NULL,
    )
    destroyed_at = models.DateTimeField(default=timezone.now)
    reason = models.TextField()
    status = models.CharField(
        max_length=20,
        choices=DestructionStatus.choices,
        default=DestructionStatus.RECORDED,
    )

    def clean(self):
        super().clean()


    def save(self, *args, **kwargs):
        applying = getattr(self, "_applying", False)

        if not applying:
            if self.pk is None:
                if self.status != self.DestructionStatus.RECORDED:
                    raise ValidationError(
                        "Une destruction doit être enregistrée "
                        "avant son exécution."
                    )
            else:
                previous = (
                    type(self).objects
                    .only("status")
                    .get(pk=self.pk)
                )

                if previous.status == self.DestructionStatus.COMPLETED:
                    raise ValidationError(
                        "Une destruction terminée ne peut pas "
                        "être modifiée."
                    )

                if self.status == self.DestructionStatus.COMPLETED:
                    raise ValidationError(
                        "Le statut COMPLETED ne peut être attribué "
                        "que par la méthode apply()."
                    )

        self.full_clean()
        return super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        if self.status == self.DestructionStatus.COMPLETED:
            raise ValidationError(
                "Une destruction terminée ne peut pas être supprimée."
            )

        return super().delete(*args, **kwargs)

    @transaction.atomic
    def apply(self):
        if not self.pk:
            raise ValidationError(
                "Le document de destruction doit être enregistré "
                "avant son exécution."
            )

        # Verrouiller le document pour empêcher deux exécutions
        # simultanées de la même destruction.
        destruction = (
            StockDestruction.objects
            .select_for_update()
            .get(pk=self.pk)
        )

        if destruction.status == self.DestructionStatus.COMPLETED:
            raise ValidationError(
                "Cette destruction a déjà été exécutée."
            )

        if destruction.status != self.DestructionStatus.RECORDED:
            raise ValidationError(
                "Le statut du document ne permet pas son exécution."
            )

        destruction.full_clean()

        # Les lignes sont lues après le verrouillage du document.
        # Leur enregistrement verrouille également leur document parent.
        lines = list(
            StockDestructionLine.objects
            .filter(destruction_id=destruction.pk)
            .order_by("pk")
        )

        if not lines:
            raise ValidationError(
                "Une destruction doit contenir au moins une ligne."
            )

        # Une destruction doit identifier explicitement le lot détruit.
        for line in lines:
            if not line.stock_entry_id:
                raise ValidationError({
                    "stock_entry": (
                        "Chaque ligne de destruction doit désigner "
                        "le lot concerné."
                    )
                })

        item_ids = {line.item_id for line in lines}
        lot_ids = {line.stock_entry_id for line in lines}

        # Toujours verrouiller les produits avant les lots,
        # comme dans StockExit.
        items = list(
            InventoryItem.objects
            .select_for_update()
            .filter(pk__in=item_ids)
            .order_by("pk")
        )
        item_map = {item.pk: item for item in items}

        lots = list(
            StockEntry.objects
            .select_for_update()
            .filter(pk__in=lot_ids)
            .order_by("pk")
        )
        lot_map = {lot.pk: lot for lot in lots}

        if len(item_map) != len(item_ids):
            raise ValidationError(
                "Un ou plusieurs produits de la destruction "
                "n'existent plus."
            )

        if len(lot_map) != len(lot_ids):
            raise ValidationError(
                "Un ou plusieurs lots de la destruction "
                "n'existent plus."
            )

        # Vérifier chaque ligne et calculer les quantités cumulées.
        # Le cumul est nécessaire si plusieurs lignes désignent
        # le même lot.
        quantities_by_lot = {}
        quantities_by_item = {}

        for line in lines:
            line.destruction = destruction
            line.item = item_map[line.item_id]
            line.stock_entry = lot_map[line.stock_entry_id]

            line.full_clean()

            lot = lot_map[line.stock_entry_id]
            item = item_map[line.item_id]

            if lot.item_id != item.pk:
                raise ValidationError({
                    "stock_entry": (
                        "Le lot ne correspond pas au produit "
                        "de la ligne de destruction."
                    )
                })

            quantities_by_lot[lot.pk] = (
                quantities_by_lot.get(
                    lot.pk,
                    line.quantity * 0,
                )
                + line.quantity
            )

            quantities_by_item[item.pk] = (
                quantities_by_item.get(
                    item.pk,
                    line.quantity * 0,
                )
                + line.quantity
            )

        # Vérifier la disponibilité de chaque lot.
        for lot_id, quantity in quantities_by_lot.items():
            lot = lot_map[lot_id]

            if quantity > lot.remaining_quantity:
                raise ValidationError({
                    "quantity": (
                        f"Quantité à détruire insuffisante pour "
                        f"le lot {lot.batch_number or lot.pk}. "
                        f"Quantité demandée : {quantity} ; "
                        f"quantité restante : {lot.remaining_quantity}."
                    )
                })

        # Vérifier également le stock physique global.
        for item_id, quantity in quantities_by_item.items():
            item = item_map[item_id]

            if quantity > item.stock_quantity:
                raise ValidationError({
                    "quantity": (
                        f"La quantité à détruire dépasse le stock "
                        f"physique de {item.name}. "
                        f"Quantité demandée : {quantity} ; "
                        f"stock enregistré : {item.stock_quantity}."
                    )
                })

        # Déduire les quantités des lots.
        for lot_id, quantity in quantities_by_lot.items():
            lot = lot_map[lot_id]
            lot.remaining_quantity -= quantity

            lot._updating_stock = True
            try:
                lot.save(
                    update_fields=[
                        "remaining_quantity",
                        "updated_at",
                    ]
                )
            finally:
                lot._updating_stock = False

        # Déduire les quantités du stock physique global.
        for item_id, quantity in quantities_by_item.items():
            item = item_map[item_id]
            item.stock_quantity -= quantity

            item.save(
                update_fields=[
                    "stock_quantity",
                    "updated_at",
                ]
            )

        # Le document n'est terminé qu'après les mouvements de stock.
        destruction.status = self.DestructionStatus.COMPLETED
        destruction._applying = True

        try:
            destruction.save(
                update_fields=[
                    "status",
                    "updated_at",
                ]
            )
        finally:
            destruction._applying = False

        for item_id in sorted(quantities_by_item):
            StockAlert.sync_for_item(item_id)

        self.status = destruction.status

        return {
            "destruction_id": destruction.pk,
            "status": destruction.status,
            "destroyed_quantities": quantities_by_item,
        }

    def __str__(self):
        return f"Destruction {self.pk}"


class StockDestructionLine(TimestampedModel):
    destruction = models.ForeignKey(
        "inventory.StockDestruction",
        related_name="lines",
        on_delete=models.PROTECT,
    )
    item = models.ForeignKey(
        "inventory.InventoryItem",
        related_name="destruction_lines",
        on_delete=models.PROTECT,
    )
    stock_entry = models.ForeignKey(
        "inventory.StockEntry",
        related_name="destruction_lines",
        null=True,
        blank=True,
        on_delete=models.PROTECT,
    )
    quantity = models.DecimalField(
        max_digits=12,
        decimal_places=2,
    )
    stock_alert = models.ForeignKey(
        "inventory.StockAlert",
        related_name="destruction_lines",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
    )

    def clean(self):
        super().clean()

        errors = {}

        if self.quantity is not None and self.quantity <= 0:
            errors["quantity"] = (
                "La quantité à détruire doit être strictement positive."
            )

        if self.stock_entry_id and self.item_id:
            if self.stock_entry.item_id != self.item_id:
                errors["stock_entry"] = (
                    "Le lot doit appartenir au produit concerné."
                )

        if self.stock_alert_id:
            alert = self.stock_alert

            if alert.alert_type != StockAlert.AlertType.EXPIRATION:
                errors["stock_alert"] = (
                    "Seule une alerte de péremption peut être associée "
                    "à une ligne de destruction."
                )

            if alert.item_id != self.item_id:
                errors["stock_alert"] = (
                    "L'alerte doit concerner le produit de la ligne."
                )

            if not self.stock_entry_id:
                errors["stock_entry"] = (
                    "Un lot doit être indiqué lorsqu'une alerte "
                    "de péremption est associée."
                )
            elif alert.stock_entry_id != self.stock_entry_id:
                errors["stock_alert"] = (
                    "L'alerte doit concerner exactement le lot détruit."
                )

        if errors:
            raise ValidationError(errors)

    @transaction.atomic
    def save(self, *args, **kwargs):
        # Verrouiller le document parent afin qu'une ligne ne puisse
        # pas être ajoutée ou modifiée pendant son exécution.
        destruction = (
            StockDestruction.objects
            .select_for_update()
            .get(pk=self.destruction_id)
        )

        if destruction.status != StockDestruction.DestructionStatus.RECORDED:
            raise ValidationError(
                "Les lignes d'une destruction terminée "
                "ne peuvent pas être modifiées."
            )

        self.full_clean()

        return super().save(*args, **kwargs)

    @transaction.atomic
    def delete(self, *args, **kwargs):
        destruction = (
            StockDestruction.objects
            .select_for_update()
            .get(pk=self.destruction_id)
        )

        if destruction.status != StockDestruction.DestructionStatus.RECORDED:
            raise ValidationError(
                "Les lignes d'une destruction terminée "
                "ne peuvent pas être supprimées."
            )

        return super().delete(*args, **kwargs)

    def __str__(self):
        return (
            f"Destruction {self.destruction_id} — "
            f"{self.item.name} — {self.quantity}"
        )
