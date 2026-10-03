from decimal import Decimal, ROUND_HALF_UP
import re
from datetime import date

from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import Sum
from django.utils import timezone

from dental_clinic.common import (
    TimestampedModel,
    SoftDeleteModel,
    ProtectedSoftDeleteManager,
)

class PrestationCategory(TimestampedModel):
    """
    Référentiel dynamique des catégories de prestations de la clinique.

    Les catégories sont configurées par l'administration via l'API.
    Le code n'utilise pas Django choices : les valeurs sont créées
    dynamiquement en base et servent ensuite de choix pour les prestations.
    """

    name = models.CharField(
        max_length=100,
        unique=True,
    )
    code = models.CharField(
        max_length=50,
        unique=True,
    )
    is_active = models.BooleanField(
        default=True,
    )

    def __str__(self):
        return f"{self.code} - {self.name}"

class Prestation(TimestampedModel):

    category = models.ForeignKey(
        'billing.PrestationCategory',
        on_delete=models.PROTECT,
        related_name='prestations',
        help_text=(
            "Famille métier à laquelle appartient la prestation. "
            "Permet de regrouper les prestations du catalogue."
            "category devait apparaitre comme une liste choix exposé sepuis PrestationCategory"
        ),
    )

    code = models.CharField(
        max_length=64,
        unique=True,
        help_text=(
            "Identifiant métier unique de la prestation. "
            "Utilisé pour identifier la prestation indépendamment de son libellé."
        ),
    )

    label = models.CharField(
        max_length=255,
        help_text=(
            "Nom de la prestation affiché aux utilisateurs "
            "dans le catalogue et les interfaces."
        ),
    )

    description = models.TextField(
        blank=True,
        help_text=(
            "Description métier de la prestation : périmètre, contenu "
            "et informations permettant de comprendre ce que couvre la prestation. "
            "Ce champ est informatif et ne constitue pas une donnée tarifaire structurée."
        ),
    )

    is_active = models.BooleanField(
        default=True,
        help_text=(
            "Indique si la prestation est actuellement disponible "
            "pour les nouvelles opérations. Une prestation inactive "
            "reste conservée pour préserver l'historique."
        ),
    )

    def __str__(self):
        return f"{self.code} - {self.label}"

class PrestationTarif(TimestampedModel):
    """
    Référentiel historique des tarifs d'une prestation.

    Chaque tarif est paramétré par l'administration avec son montant,
    son taux de taxe et sa date d'entrée en vigueur.
    Pour une prestation et une date données, le tarif applicable est
    le tarif dont effective_from est la date la plus récente qui ne
    dépasse pas la date recherchée.

    Lors de la facturation, le montant et le taux applicables sont
    copiés dans InvoiceLine afin de conserver le prix réellement
    appliqué au moment de la facturation.

    prestation doit être sélectionnée parmi les prestations existantes du catalogue ;
      le tarif est toujours rattaché à une prestation existante.

    """
    prestation = models.ForeignKey(
        'billing.Prestation',
        on_delete=models.PROTECT,
        related_name='tarifs',
    )
    amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
    )
    tax_rate = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=Decimal('0.00'),
    )
    effective_from = models.DateField(help_text="Date à partir de laquelle le tarif est applicable")

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['prestation', 'effective_from'],
                name='unique_prestation_tarif_effective_from',
            ),
        ]
        ordering = ['-effective_from']

    def clean(self):
        errors = {}

        if self.amount < 0:
            errors['amount'] = 'Le montant du tarif ne peut pas être négatif.'

        if self.tax_rate < 0:
            errors['tax_rate'] = 'Le taux de taxe ne peut pas être négatif.'

        if errors:
            raise ValidationError(errors)

    def __str__(self):
        return (
            f"{self.prestation.code} - "
            f"{self.amount} - "
            f"{self.effective_from}"
        )


class Estimate(SoftDeleteModel):
    patient = models.ForeignKey(
        'patients.Patient',
        on_delete=models.PROTECT,
        related_name='estimates',
    )
    created_by = models.ForeignKey(
        'accounts.User',
        on_delete=models.PROTECT,
        related_name='created_estimates',
    )
    validated_by = models.ForeignKey(
        'accounts.User',
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name='validated_estimates',
    )
    valid_until = models.DateField()
    total_amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
    )
    tax_amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=Decimal('0.00'),
    )
    notes = models.TextField(
        blank=True,
    )
    reference_number = models.CharField(
        max_length=64,
        unique=True,
    )
    related_treatment_plan = models.ForeignKey(
        'treatment_plans.TreatmentPlan',
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name='estimates',
    )

    def clean(self):
        errors = {}

        if self.total_amount < 0:
            errors['total_amount'] = (
                'Le montant total ne peut pas être négatif.'
            )

        if self.tax_amount < 0:
            errors['tax_amount'] = (
                'Le montant de taxe ne peut pas être négatif.'
            )

        if self.tax_amount > self.total_amount:
            errors['tax_amount'] = (
                'La taxe ne peut pas dépasser le montant total.'
            )

        if errors:
            raise ValidationError(errors)

    def __str__(self):
        return self.reference_number

class Invoice(SoftDeleteModel):
    class Status(models.TextChoices):
        DRAFT = 'draft', 'Draft'
        ISSUED = 'issued', 'Issued'
        COMPLETED = 'completed', 'Completed'

    objects = ProtectedSoftDeleteManager()

    patient = models.ForeignKey(
        'patients.Patient',
        on_delete=models.PROTECT,
        related_name='invoices',
    )
    created_by = models.ForeignKey(
        'accounts.User',
        on_delete=models.PROTECT,
        related_name='created_invoices',
    )

    issued_at = models.DateField()
    due_date = models.DateField()

    status = models.CharField(
        max_length=32,
        choices=Status.choices,
        default=Status.DRAFT,
    )

    subtotal = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=Decimal('0.00'),
    )
    tax_amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=Decimal('0.00'),
    )
    total_amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=Decimal('0.00'),
    )
    credit_amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=Decimal('0.00'),
    )
    paid_amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=Decimal('0.00'),
    )
    balance_due = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=Decimal('0.00'),
    )

    reference_number = models.CharField(
        max_length=64,
        unique=True,
    )
    notes = models.TextField(
        blank=True,
    )

    def clean(self):
        errors = {}

        if self.due_date < self.issued_at:
            errors['due_date'] = (
                "La date d'échéance ne peut pas être antérieure "
                "à la date d'émission."
            )

        financial_fields = {
            'subtotal': self.subtotal,
            'tax_amount': self.tax_amount,
            'total_amount': self.total_amount,
            'credit_amount': self.credit_amount,
            'paid_amount': self.paid_amount,
            'balance_due': self.balance_due,
        }

        for field_name, value in financial_fields.items():
            if value < Decimal('0.00'):
                errors[field_name] = (
                    'Le montant ne peut pas être négatif.'
                )

        if (
            self.credit_amount + self.paid_amount
            > self.total_amount
        ):
            errors['balance_due'] = (
                'Le montant crédité et le montant payé ne peuvent pas '
                'dépasser le montant total de la facture.'
            )

        if errors:
            raise ValidationError(errors)

    def recalculate_financials(self):
        subtotal = Decimal('0.00')
        tax_amount = Decimal('0.00')
        total_amount = Decimal('0.00')

        for line in self.lines.all():
            subtotal += line.subtotal
            tax_amount += line.tax_amount
            total_amount += line.total

        payment_totals = self.payments.aggregate(
            total=Sum('amount'),
        )

        credit_totals = self.credit_notes.aggregate(
            total=Sum('amount'),
        )

        self.subtotal = subtotal.quantize(
            Decimal('0.01'),
            rounding=ROUND_HALF_UP,
        )

        self.tax_amount = tax_amount.quantize(
            Decimal('0.01'),
            rounding=ROUND_HALF_UP,
        )

        self.total_amount = total_amount.quantize(
            Decimal('0.01'),
            rounding=ROUND_HALF_UP,
        )

        self.paid_amount = (
            payment_totals['total']
            or Decimal('0.00')
        ).quantize(
            Decimal('0.01'),
            rounding=ROUND_HALF_UP,
        )

        self.credit_amount = (
            credit_totals['total']
            or Decimal('0.00')
        ).quantize(
            Decimal('0.01'),
            rounding=ROUND_HALF_UP,
        )

        self.balance_due = (
            self.total_amount
            - self.credit_amount
            - self.paid_amount
        ).quantize(
            Decimal('0.01'),
            rounding=ROUND_HALF_UP,
        )

        if self.balance_due < Decimal('0.00'):
            raise ValidationError(
                'Le solde de la facture ne peut pas être négatif.'
            )

        if (
            self.total_amount != Decimal('0.00')
            and self.balance_due == Decimal('0.00')
        ):
            self.status = self.Status.COMPLETED

    @classmethod
    def generate_reference_number(cls, invoice_date):
        year = invoice_date.year

        references = cls.objects.filter(
            reference_number__endswith=f"/{year}"
        ).values_list("reference_number", flat=True)

        if not references:
            return f"A0001/{year}"

        pattern = re.compile(
            rf"^(?P<letters>[A-Z]+)(?P<number>\d+)/{year}$"
        )

        last_letters = None
        last_number = None

        for reference in references:
            match = pattern.match(reference)

            if not match:
                continue

            letters = match.group("letters")
            number = int(match.group("number"))

            if (
                last_letters is None
                or (len(letters), letters, number)
                > (len(last_letters), last_letters, last_number)
            ):
                last_letters = letters
                last_number = number

        if last_letters is None:
            return f"A0001/{year}"

        # Nombre de chiffres disponibles selon le nombre de lettres.
        digit_count = 5 - len(last_letters)

        # On est arrivé à la fin de cette série :
        # A0001 ... Z9999
        # AA001 ... ZZ999
        # AAA01 ... ZZZ99
        # AAAA1 ... ZZZZ9
        if last_number >= (10 ** digit_count) - 1:
            next_letters = cls._increment_letters(last_letters)

            # Après Z -> AA, le compteur recommence à 1.
            return f"{next_letters}{1:0{digit_count - 1}d}/{year}"

        next_number = last_number + 1

        return (
            f"{last_letters}"
            f"{next_number:0{digit_count}d}"
            f"/{year}"
        )

    @staticmethod
    def _increment_letters(letters):
        letters = list(letters)
        position = len(letters) - 1

        while position >= 0:
            if letters[position] != "Z":
                letters[position] = chr(ord(letters[position]) + 1)
                return "".join(letters)

            letters[position] = "A"
            position -= 1

        return "A" + "".join(letters)


    def __str__(self):
        return self.reference_number

class InvoiceLine(TimestampedModel):
    invoice = models.ForeignKey(
        'billing.Invoice',
        on_delete=models.CASCADE,
        related_name='lines',
        null=True,
        blank=True,
    )
    treatment = models.ForeignKey(
        'treatments.Treatment',
        on_delete=models.PROTECT,
        related_name='invoice_lines',
    )
    prestation = models.ForeignKey(
        'billing.Prestation',
        on_delete=models.PROTECT,
        related_name='billing_invoice_lines',
    )
    description = models.CharField(
        max_length=255,
    )
    quantity = models.DecimalField(
        max_digits=10,
        decimal_places=2,
    )
    unit_price = models.DecimalField(
        max_digits=12,
        decimal_places=2,
    )
    tax_rate = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=Decimal('0.00'),
    )

    @property
    def subtotal(self):
        return (
            self.quantity * self.unit_price
        ).quantize(
            Decimal('0.01'),
            rounding=ROUND_HALF_UP,
        )

    @property
    def tax_amount(self):
        return (
            self.subtotal
            * self.tax_rate
            / Decimal('100')
        ).quantize(
            Decimal('0.01'),
            rounding=ROUND_HALF_UP,
        )

    @property
    def total(self):
        return (
            self.subtotal + self.tax_amount
        ).quantize(
            Decimal('0.01'),
            rounding=ROUND_HALF_UP,
        )

    def clean(self):
        errors = {}

        if self.quantity <= 0:
            errors['quantity'] = (
                'La quantité doit être strictement positive.'
            )

        if self.unit_price < 0:
            errors['unit_price'] = (
                'Le prix unitaire ne peut pas être négatif.'
            )

        if self.tax_rate < 0:
            errors['tax_rate'] = (
                'Le taux de taxe ne peut pas être négatif.'
            )

        if self.treatment_id and self.prestation_id:
            if self.treatment.prestation_id != self.prestation_id:
                errors['prestation'] = (
                    "La prestation de la ligne doit correspondre "
                    "à la prestation du traitement."
                )

        if self.invoice_id and self.treatment_id:
            if self.treatment.patient_id != self.invoice.patient_id:
                errors['treatment'] = (
                    "Le patient du traitement doit correspondre "
                    "au patient de la facture."
                )

        if self.pk:
            previous_invoice_id = (
                InvoiceLine.objects
                .filter(pk=self.pk)
                .values_list('invoice_id', flat=True)
                .first()
            )

            if (
                previous_invoice_id is not None
                and previous_invoice_id != self.invoice_id
            ):
                errors['invoice'] = (
                    'La ligne de facture ne peut pas être transférée '
                    'vers une autre facture.'
                )

        if errors:
            raise ValidationError(errors)

    def delete(self, *args, **kwargs):
        invoice = self.invoice

        result = super().delete(*args, **kwargs)

        invoice.recalculate_financials()
        invoice.save(
            update_fields=[
                'subtotal',
                'tax_amount',
                'total_amount',
                'credit_amount',
                'paid_amount',
                'balance_due',
                'status',
            ]
        )

        return result

    def get_applicable_pricing(self):
        reference_date = self.treatment.start_at.date()

        tarif = (
            self.prestation.tarifs
            .filter(
                effective_from__lte=reference_date,
            )
            .order_by('-effective_from')
            .first()
        )

        if tarif is None:
            return None

        return {
            'unit_price': tarif.amount,
            'tax_rate': tarif.tax_rate,
        }

    def save(self, *args, **kwargs):
        pricing = self.get_applicable_pricing()

        if pricing is None:
            raise ValidationError({
                'unit_price': (
                    'Aucun tarif applicable n’existe pour cette prestation '
                    'à la date du traitement.'
                )
            })

        self.unit_price = pricing['unit_price']
        self.tax_rate = pricing['tax_rate']

        # Valider d'abord la ligne
        self.full_clean()

        # Première InvoiceLine :
        # aucune Invoice n'existe encore, on l'initialise.

        if self.invoice_id is None:
            invoice_date = self.treatment.start_at.date()

            self.invoice = Invoice.objects.create(
                patient=self.treatment.patient,
                created_by=self.treatment.dentist,
                issued_at=invoice_date,
                due_date=invoice_date,
                status=Invoice.Status.ISSUED,
                reference_number=Invoice.generate_reference_number(
                    invoice_date
                ),
            )
        # Maintenant invoice existe obligatoirement
        result = super().save(*args, **kwargs)

        self.invoice.recalculate_financials()

        self.invoice.save(
            update_fields=[
                'subtotal',
                'tax_amount',
                'total_amount',
                'credit_amount',
                'paid_amount',
                'balance_due',
                'status',
            ]
        )

        return result

class Payment(TimestampedModel):
    class Status(models.TextChoices):
        COMPLETED = 'completed', 'Completed'

    invoice = models.ForeignKey(
        'billing.Invoice',
        on_delete=models.PROTECT,
        related_name='payments',
    )
    patient = models.ForeignKey(
        'patients.Patient',
        on_delete=models.PROTECT,
        related_name='payments',
    )
    paid_by = models.ForeignKey(
        'accounts.User',
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name='payments_received',
    )
    payment_at = models.DateTimeField(
        default=timezone.now,
    )
    amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
    )
    method = models.ForeignKey(
        'billing.PaymentMethod',
        on_delete=models.PROTECT,
        related_name='payments',
    )
    reference = models.CharField(
        max_length=255,
        blank=True,
    )
    status = models.CharField(
        max_length=32,
        choices=Status.choices,
        default=Status.COMPLETED,
    )

    def clean(self):
        errors = {}

        if self.amount <= 0:
            errors['amount'] = (
                'Le montant du paiement doit être strictement positif.'
            )

        if self.invoice_id and self.patient_id:
            if self.invoice.patient_id != self.patient_id:
                errors['patient'] = (
                    'Le patient du paiement doit correspondre '
                    'au patient de la facture.'
                )

        if self.invoice_id and self.amount > 0:
            balance = self.invoice.balance_due

            if self.pk:
                previous_amount = (
                    Payment.objects
                    .filter(pk=self.pk)
                    .values_list('amount', flat=True)
                    .first()
                )

                if previous_amount:
                    balance += previous_amount

            if self.amount > balance:
                errors['amount'] = (
                    'Le paiement ne peut pas dépasser '
                    'le solde restant de la facture.'
                )

        if errors:
            raise ValidationError(errors)

    def delete(self, *args, **kwargs):
        invoice = self.invoice

        result = super().delete(*args, **kwargs)

        invoice.recalculate_financials()
        invoice.save(
            update_fields=[
                'subtotal',
                'tax_amount',
                'total_amount',
                'credit_amount',
                'paid_amount',
                'balance_due',
                'status',
            ]
        )

        return result

    def save(self, *args, **kwargs):
        self.full_clean()

        result = super().save(*args, **kwargs)

        self.invoice.recalculate_financials()
        self.invoice.save(
            update_fields=[
                'subtotal',
                'tax_amount',
                'total_amount',
                'credit_amount',
                'paid_amount',
                'balance_due',
                'status',
            ]
        )

        return result

    def __str__(self):
        return f"{self.amount} - {self.invoice.reference_number}"


class CreditNote(TimestampedModel):
    class Status(models.TextChoices):
        COMPLETED = 'completed', 'Completed'

    invoice = models.ForeignKey(
        'billing.Invoice',
        on_delete=models.PROTECT,
        related_name='credit_notes',
    )
    created_by = models.ForeignKey(
        'accounts.User',
        on_delete=models.PROTECT,
        related_name='created_credit_notes',
    )
    issued_at = models.DateField(
        default=timezone.localdate,
    )
    amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
    )
    reason = models.TextField()
    status = models.CharField(
        max_length=32,
        choices=Status.choices,
        default=Status.COMPLETED,
    )

    def clean(self):
        errors = {}

        if self.amount <= 0:
            errors['amount'] = (
                "Le montant de l'avoir doit être strictement positif."
            )

        if self.invoice_id and self.amount > 0:
            credited = (
                self.invoice.credit_amount
                or Decimal('0.00')
            )

            if self.pk:
                previous_amount = (
                    CreditNote.objects
                    .filter(pk=self.pk)
                    .values_list('amount', flat=True)
                    .first()
                )

                if previous_amount:
                    credited -= previous_amount

            available = (
                self.invoice.total_amount
                - credited
                - self.invoice.paid_amount
            )

            if self.amount > available:
                errors['amount'] = (
                    "L'avoir ne peut pas dépasser "
                    "le montant encore disponible."
                )

        if errors:
            raise ValidationError(errors)

    def delete(self, *args, **kwargs):
        invoice = self.invoice

        result = super().delete(*args, **kwargs)

        invoice.recalculate_financials()
        invoice.save(
            update_fields=[
                'subtotal',
                'tax_amount',
                'total_amount',
                'credit_amount',
                'paid_amount',
                'balance_due',
                'status',
            ]
        )

        return result

    def save(self, *args, **kwargs):
        self.full_clean()

        result = super().save(*args, **kwargs)

        self.invoice.recalculate_financials()
        self.invoice.save(
            update_fields=[
                'subtotal',
                'tax_amount',
                'total_amount',
                'credit_amount',
                'paid_amount',
                'balance_due',
                'status',
            ]
        )

        return result

    def __str__(self):
        return f"Avoir {self.amount} - {self.invoice.reference_number}"


class PaymentMethod(TimestampedModel):
    name = models.CharField(
        max_length=100,
        unique=True,
    )
    provider = models.CharField(
        max_length=100,
        blank=True,
    )
    details = models.JSONField(
        default=dict,
        blank=True,
    )
    is_active = models.BooleanField(
        default=True,
    )

    def __str__(self):
        return self.name