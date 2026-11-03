from decimal import Decimal, ROUND_HALF_UP
import re
from datetime import date

from django.core.exceptions import ValidationError
from django.db import models, transaction
from django.db.models import Sum
from django.utils import timezone

from appointments.models import Appointment

from dental_clinic.common import (
    TimestampedModel,
    SoftDeleteModel,
    ProtectedSoftDeleteManager,
)


def _lock_invoices(*invoice_ids):
    locked = {}
    for invoice_id in sorted(set(filter(None, invoice_ids))):
        locked[invoice_id] = Invoice.all_objects.select_for_update().get(
            pk=invoice_id,
        )
    return locked


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
        with transaction.atomic():
            locked_invoice = (
                Invoice.all_objects
                .select_for_update()
                .get(pk=self.pk)
            )
            self.status = locked_invoice.status

            self._recalculate_financials_locked()

    def _recalculate_financials_locked(self):
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

    def save(self, *args, **kwargs):
        if self._state.adding and not self.reference_number:
            invoice_date = self.issued_at
            if isinstance(invoice_date, str):
                invoice_date = date.fromisoformat(invoice_date)
                self.issued_at = invoice_date

            using = kwargs.get('using') or self._state.db
            with transaction.atomic(using=using):
                with transaction.get_connection(using).cursor() as cursor:
                    cursor.execute(
                        "SELECT pg_advisory_xact_lock(%s, %s)",
                        [0x44454E54, invoice_date.year],
                    )

                self.reference_number = self.generate_reference_number(
                    invoice_date,
                )
                return super().save(*args, **kwargs)

        return super().save(*args, **kwargs)

    @classmethod
    def generate_reference_number(cls, invoice_date):
        year = invoice_date.year

        references = cls.all_objects.filter(
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
        with transaction.atomic():
            invoice_id = self.invoice_id
            if invoice_id is None:
                return super().delete(*args, **kwargs)

            invoice = Invoice.all_objects.select_for_update().get(
                pk=invoice_id,
            )
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

    def _create_invoice_for_treatment(self):
        invoice_date = self.treatment.start_at.date()

        return Invoice.objects.create(
            patient=self.treatment.patient,
            created_by=self.treatment.dentist,
            issued_at=invoice_date,
            due_date=invoice_date,
            status=Invoice.Status.ISSUED,
        )

    def _get_or_create_invoice(self):
        """
        Facture regroupant les traitements d'un même rendez-vous.

        The caller holds a transaction open, so the appointment lock also
        protects the subsequent InvoiceLine insert.
        """
        appointment_id = self.treatment.appointment_id

        if appointment_id is None:
            return self._create_invoice_for_treatment()

        try:
            Appointment.objects.select_for_update().get(pk=appointment_id)
        except Appointment.DoesNotExist as error:
            raise ValidationError({
                'treatment': (
                    "Le rendez-vous associé au traitement n'existe plus."
                )
            }) from error

        provided_invoice = None
        if self.invoice_id is not None:
            provided_invoice = (
                Invoice.all_objects
                .select_for_update()
                .filter(pk=self.invoice_id)
                .first()
            )
            if provided_invoice is None:
                raise ValidationError({
                    'invoice': "La facture fournie n'existe pas."
                })
            if provided_invoice.is_deleted:
                raise ValidationError({
                    'invoice': (
                        "Une facture archivée ne peut pas recevoir de "
                        "nouvelle ligne."
                    )
                })

        invoice_ids = list(
            Invoice.all_objects
            .filter(lines__treatment__appointment_id=appointment_id)
            .order_by('pk')
            .values_list('pk', flat=True)
            .distinct()[:2]
        )

        if len(invoice_ids) > 1:
            raise ValidationError({
                'invoice': (
                    "Les traitements de ce rendez-vous sont déjà répartis "
                    "sur plusieurs factures. La facturation est bloquée "
                    "pour préserver leur cohérence."
                )
            })

        if invoice_ids:
            expected_invoice_id = invoice_ids[0]
            if (
                self.invoice_id is not None
                and self.invoice_id != expected_invoice_id
            ):
                raise ValidationError({
                    'invoice': (
                        "La facture fournie ne correspond pas à la facture "
                        "de regroupement de ce rendez-vous."
                    )
                })

            invoice = (
                provided_invoice
                if provided_invoice is not None
                else _lock_invoices(expected_invoice_id)[expected_invoice_id]
            )
            if invoice.is_deleted:
                raise ValidationError({
                    'invoice': (
                        "La facture de regroupement de ce rendez-vous est "
                        "archivée et ne peut pas recevoir de nouvelle ligne."
                    )
                })
            return invoice

        if self.invoice_id is not None:
            provided_invoice = _lock_invoices(self.invoice_id)[self.invoice_id]
            if provided_invoice.lines.exclude(
                treatment__appointment_id=appointment_id,
            ).exists():
                raise ValidationError({
                    'invoice': (
                        "La facture fournie contient déjà des lignes "
                        "associées à un autre rendez-vous."
                    )
                })
            return provided_invoice

        return self._create_invoice_for_treatment()

    def save(self, *args, **kwargs):
        with transaction.atomic():
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

            if self.treatment.appointment_id is not None:
                self.invoice = self._get_or_create_invoice()
            elif self.invoice_id is None:
                self.invoice = self._create_invoice_for_treatment()
            else:
                self.invoice = _lock_invoices(self.invoice_id)[
                    self.invoice_id
                ]

            # Validate after assigning the actual invoice so patient and
            # appointment consistency are checked against persisted values.
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
                previous_payment = (
                    Payment.objects
                    .filter(pk=self.pk)
                    .values('amount', 'invoice_id')
                    .first()
                )

                if (
                    previous_payment is not None
                    and previous_payment['invoice_id'] == self.invoice_id
                ):
                    balance += previous_payment['amount']

            if self.amount > balance:
                errors['amount'] = (
                    'Le paiement ne peut pas dépasser '
                    'le solde restant de la facture.'
                )

        if errors:
            raise ValidationError(errors)

    def delete(self, *args, **kwargs):
        with transaction.atomic():
            persisted_invoice_id = (
                Payment.objects
                .filter(pk=self.pk)
                .values_list('invoice_id', flat=True)
                .first()
            )
            invoice = _lock_invoices(persisted_invoice_id)[
                persisted_invoice_id
            ]
            payment = Payment.objects.select_for_update().get(pk=self.pk)
            if payment.invoice_id != persisted_invoice_id:
                raise ValidationError(
                    "Le paiement a changé de facture pendant sa suppression."
                )

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
        with transaction.atomic():
            if self.invoice_id is None:
                self.full_clean()

            previous_invoice_id = None
            if self.pk is not None:
                previous_invoice_id = (
                    Payment.objects
                    .filter(pk=self.pk)
                    .values_list('invoice_id', flat=True)
                    .first()
                )

            locked_invoices = _lock_invoices(
                previous_invoice_id,
                self.invoice_id,
            )
            invoice = locked_invoices[self.invoice_id]
            self.invoice = invoice

            if self.pk is not None:
                persisted_payment = (
                    Payment.objects
                    .select_for_update()
                    .get(pk=self.pk)
                )
                if persisted_payment.invoice_id != previous_invoice_id:
                    raise ValidationError(
                        "Le paiement a changé de facture pendant sa modification."
                    )

            invoice.recalculate_financials()
            self.full_clean()
            result = super().save(*args, **kwargs)

            for locked_invoice in locked_invoices.values():
                locked_invoice.recalculate_financials()
                locked_invoice.save(
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
                previous_credit = (
                    CreditNote.objects
                    .filter(pk=self.pk)
                    .values('amount', 'invoice_id')
                    .first()
                )

                if (
                    previous_credit is not None
                    and previous_credit['invoice_id'] == self.invoice_id
                ):
                    credited -= previous_credit['amount']

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
        with transaction.atomic():
            persisted_invoice_id = (
                CreditNote.objects
                .filter(pk=self.pk)
                .values_list('invoice_id', flat=True)
                .first()
            )
            invoice = _lock_invoices(persisted_invoice_id)[
                persisted_invoice_id
            ]
            credit_note = CreditNote.objects.select_for_update().get(pk=self.pk)
            if credit_note.invoice_id != persisted_invoice_id:
                raise ValidationError(
                    "L'avoir a changé de facture pendant sa suppression."
                )

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
        with transaction.atomic():
            if self.invoice_id is None:
                self.full_clean()

            previous_invoice_id = None
            if self.pk is not None:
                previous_invoice_id = (
                    CreditNote.objects
                    .filter(pk=self.pk)
                    .values_list('invoice_id', flat=True)
                    .first()
                )

            locked_invoices = _lock_invoices(
                previous_invoice_id,
                self.invoice_id,
            )
            invoice = locked_invoices[self.invoice_id]
            self.invoice = invoice

            if self.pk is not None:
                persisted_credit = (
                    CreditNote.objects
                    .select_for_update()
                    .get(pk=self.pk)
                )
                if persisted_credit.invoice_id != previous_invoice_id:
                    raise ValidationError(
                        "L'avoir a changé de facture pendant sa modification."
                    )

            invoice.recalculate_financials()
            self.full_clean()
            result = super().save(*args, **kwargs)

            for locked_invoice in locked_invoices.values():
                locked_invoice.recalculate_financials()
                locked_invoice.save(
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