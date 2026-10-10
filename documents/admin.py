from django.contrib import admin
from .models import (
    Document,
    DocumentTemplate,
    DocumentTemplateVersion,
    DocumentType,
)

admin.site.register(DocumentType)
admin.site.register(DocumentTemplate)
admin.site.register(DocumentTemplateVersion)
admin.site.register(Document)
