from django.db import models
from dental_clinic.common import TimestampedModel


class Estimate(TimestampedModel):
    patient = models.ForeignKey('patients.Patient', related_name='estimates', on_delete=models.CASCADE)
    created_by = models.ForeignKey('accounts.User', null=True, blank=True, on_delete=models.SET_NULL)
    status = models.CharField(max_length=32)
    valid_until = models.DateField()
    total_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    tax_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    notes = models.TextField(blank=True)
    reference_number = models.CharField(max_length=64, unique=True)
    related_treatment_plan = models.ForeignKey('treatment_plans.TreatmentPlan', null=True, blank=True, on_delete=models.SET_NULL)


class Invoice(TimestampedModel):
    patient = models.ForeignKey('patients.Patient', related_name='invoices', on_delete=models.CASCADE)
    created_by = models.ForeignKey('accounts.User', null=True, blank=True, on_delete=models.SET_NULL)
    issued_at = models.DateField()
    due_date = models.DateField()
    status = models.CharField(max_length=32)
    total_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    tax_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    paid_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    balance_due = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    reference_number = models.CharField(max_length=64, unique=True)
    notes = models.TextField(blank=True)
    related_estimate = models.ForeignKey('billing.Estimate', null=True, blank=True, on_delete=models.SET_NULL)
    related_treatment_plan = models.ForeignKey('treatment_plans.TreatmentPlan', null=True, blank=True, on_delete=models.SET_NULL)


class InvoiceLine(TimestampedModel):
    invoice = models.ForeignKey('billing.Invoice', related_name='lines', on_delete=models.CASCADE)
    description = models.TextField()
    treatment = models.ForeignKey('treatments.Treatment', null=True, blank=True, on_delete=models.SET_NULL)
    quantity = models.DecimalField(max_digits=10, decimal_places=2, default=1)
    unit_price = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    total_price = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    tax_rate = models.DecimalField(max_digits=5, decimal_places=2, default=0)


class Payment(TimestampedModel):
    invoice = models.ForeignKey('billing.Invoice', related_name='payments', on_delete=models.CASCADE)
    patient = models.ForeignKey('patients.Patient', on_delete=models.CASCADE)
    paid_by = models.ForeignKey('accounts.User', null=True, blank=True, on_delete=models.SET_NULL)
    payment_at = models.DateTimeField()
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    method = models.CharField(max_length=64)
    reference = models.CharField(max_length=128, blank=True)
    status = models.CharField(max_length=32)


class CreditNote(TimestampedModel):
    invoice = models.ForeignKey('billing.Invoice', related_name='credit_notes', on_delete=models.CASCADE)
    created_by = models.ForeignKey('accounts.User', null=True, blank=True, on_delete=models.SET_NULL)
    issued_at = models.DateField()
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    reason = models.TextField()
    status = models.CharField(max_length=32)


class PaymentMethod(models.Model):
    name = models.CharField(max_length=128)
    provider = models.CharField(max_length=128, blank=True)
    details = models.JSONField(default=dict, blank=True)
    is_active = models.BooleanField(default=True)
