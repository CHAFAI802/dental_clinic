from django.contrib import admin
from .models import PrescriptionTemplate, Prescription

admin.site.register(PrescriptionTemplate)
admin.site.register(Prescription)
