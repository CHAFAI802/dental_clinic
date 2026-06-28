from django.db import models
from dental_clinic.common import TimestampedModel, SoftDeleteModel


class TreatmentPlan(SoftDeleteModel):
    patient = models.ForeignKey('patients.Patient', related_name='treatment_plans', on_delete=models.CASCADE)
    created_by = models.ForeignKey('accounts.User', null=True, blank=True, on_delete=models.SET_NULL)
    status = models.CharField(max_length=32)
    total_estimated_cost = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    total_approved_cost = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    patient_approved_at = models.DateTimeField(null=True, blank=True)
    notes = models.TextField(blank=True)
    version = models.PositiveIntegerField(default=1)

    def __str__(self):
        return f'Plan {self.patient} v{self.version}'


class TreatmentPlanStage(TimestampedModel):
    treatment_plan = models.ForeignKey('treatment_plans.TreatmentPlan', related_name='stages', on_delete=models.CASCADE)
    sequence = models.PositiveIntegerField()
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    planned_date = models.DateField(null=True, blank=True)
    estimated_cost = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    status = models.CharField(max_length=32)
    approval_required = models.BooleanField(default=False)
    notes = models.TextField(blank=True)

    class Meta:
        ordering = ['sequence']


class TreatmentPlanItem(TimestampedModel):
    stage = models.ForeignKey('treatment_plans.TreatmentPlanStage', related_name='items', on_delete=models.CASCADE)
    treatment_template = models.ForeignKey('treatments.TreatmentTemplate', null=True, blank=True, on_delete=models.SET_NULL)
    custom_label = models.CharField(max_length=255)
    quantity = models.PositiveIntegerField(default=1)
    unit_price = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    total_price = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    expected_duration_minutes = models.PositiveIntegerField(null=True, blank=True)
    notes = models.TextField(blank=True)


class TreatmentPlanApproval(TimestampedModel):
    treatment_plan = models.ForeignKey('treatment_plans.TreatmentPlan', related_name='approvals', on_delete=models.CASCADE)
    patient = models.ForeignKey('patients.Patient', on_delete=models.CASCADE)
    approved_by = models.ForeignKey('accounts.User', null=True, blank=True, on_delete=models.SET_NULL)
    approved_at = models.DateTimeField()
    signature_type = models.CharField(max_length=64)
    notes = models.TextField(blank=True)
