from django.contrib import admin
from .models import ImagingStudy, ImagingInstance

admin.site.register(ImagingStudy)
admin.site.register(ImagingInstance)
