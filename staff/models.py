from django.db import models
from dental_clinic.common import TimestampedModel


class StaffProfile(TimestampedModel):
    user = models.OneToOneField('accounts.User', related_name='staff_profile', on_delete=models.CASCADE)
    employee_number = models.CharField(max_length=64, unique=True)
    hire_date = models.DateField()
    end_date = models.DateField(null=True, blank=True)
    department = models.CharField(max_length=128)
    job_title = models.CharField(max_length=128)
    employment_type = models.CharField(max_length=64)
    manager = models.ForeignKey('staff.StaffProfile', null=True, blank=True, related_name='team_members', on_delete=models.SET_NULL)
    work_hours = models.JSONField(default=list, blank=True)
    base_salary = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    status = models.CharField(max_length=32)
    notes = models.TextField(blank=True)

    def __str__(self):
        return self.employee_number


class Contract(TimestampedModel):
    staff = models.ForeignKey('staff.StaffProfile', related_name='contracts', on_delete=models.CASCADE)
    contract_type = models.CharField(max_length=128)
    start_date = models.DateField()
    end_date = models.DateField(null=True, blank=True)
    salary = models.DecimalField(max_digits=12, decimal_places=2)
    working_time = models.CharField(max_length=64)
    status = models.CharField(max_length=32)


class WorkSchedule(models.Model):
    staff = models.ForeignKey('staff.StaffProfile', related_name='schedules', on_delete=models.CASCADE)
    weekday = models.IntegerField()
    start_time = models.TimeField()
    end_time = models.TimeField()
    is_active = models.BooleanField(default=True)


class AttendanceRecord(TimestampedModel):
    staff = models.ForeignKey('staff.StaffProfile', related_name='attendance_records', on_delete=models.CASCADE)
    date = models.DateField()
    clock_in = models.DateTimeField(null=True, blank=True)
    clock_out = models.DateTimeField(null=True, blank=True)
    worked_hours = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    status = models.CharField(max_length=32)
    notes = models.TextField(blank=True)


class LeaveRequest(TimestampedModel):
    staff = models.ForeignKey('staff.StaffProfile', related_name='leave_requests', on_delete=models.CASCADE)
    request_date = models.DateField()
    leave_type = models.CharField(max_length=128)
    start_date = models.DateField()
    end_date = models.DateField()
    status = models.CharField(max_length=32)
    approved_by = models.ForeignKey('accounts.User', null=True, blank=True, on_delete=models.SET_NULL)
    approved_at = models.DateTimeField(null=True, blank=True)
    notes = models.TextField(blank=True)


class StaffHistory(TimestampedModel):
    staff = models.ForeignKey('staff.StaffProfile', related_name='history', on_delete=models.CASCADE)
    changed_by = models.ForeignKey('accounts.User', null=True, blank=True, on_delete=models.SET_NULL)
    changes = models.JSONField(default=dict, blank=True)
    note = models.TextField(blank=True)
