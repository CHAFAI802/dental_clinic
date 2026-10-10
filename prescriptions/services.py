from uuid import uuid4

from django.core.files.base import ContentFile
from django.utils import timezone

from documents.docx import render_docx
from documents.storage import private_document_storage


_RESERVED_CONTEXT_KEYS = {'patient', 'dentist', 'prescription', 'generated_at'}


def build_prescription_context(prescription, generated_at=None):
    generated_at = generated_at or timezone.now()
    patient = prescription.patient
    dentist = prescription.dentist

    context = {
        'patient': {
            'first_name': patient.first_name,
            'last_name': patient.last_name,
            'middle_name': patient.middle_name,
            'patient_code': patient.patient_code,
            'birthdate': patient.birthdate.isoformat() if patient.birthdate else '',
        },
        'dentist': {
            'first_name': dentist.first_name,
            'last_name': dentist.last_name,
            'email': dentist.email,
        },
        'prescription': {
            'id': prescription.pk,
            'notes': prescription.notes,
            'created_at': prescription.created_at.isoformat(),
            'status': prescription.status,
        },
        'generated_at': timezone.localtime(generated_at).strftime('%d/%m/%Y'),
    }

    if not isinstance(prescription.filled_data, dict):
        raise ValueError('Les données de prescription doivent être un objet JSON.')

    reserved_collisions = _RESERVED_CONTEXT_KEYS.intersection(prescription.filled_data)
    if reserved_collisions:
        names = ', '.join(sorted(reserved_collisions))
        raise ValueError(f'Clés filled_data réservées au contexte : {names}.')

    context.update(prescription.filled_data)
    return context, generated_at


def generate_prescription_docx(prescription):
    template = prescription.template
    if not template.is_active:
        raise ValueError('Le template de prescription est inactif.')
    if not template.docx_file:
        raise ValueError('Aucun template DOCX n’est associé à cette prescription.')

    generated_at = timezone.now()
    context, generated_at = build_prescription_context(prescription, generated_at)

    with template.docx_file.open('rb') as template_file:
        template_bytes = template_file.read()

    rendered_bytes = render_docx(template_bytes, template.variables, context)
    filename = f'prescription-{prescription.pk}-{uuid4().hex}.docx'
    previous_name = prescription.generated_docx.name

    try:
        prescription.generated_docx.save(
            filename,
            ContentFile(rendered_bytes),
            save=False,
        )
        prescription.generated_at = generated_at
        prescription.status = prescription.Status.GENERATED
        prescription.save(
            update_fields=[
                'generated_docx',
                'generated_at',
                'status',
                'updated_at',
            ]
        )
    except Exception:
        if prescription.generated_docx.name:
            private_document_storage.delete(prescription.generated_docx.name)
        prescription.refresh_from_db()
        raise

    if previous_name and previous_name != prescription.generated_docx.name:
        private_document_storage.delete(previous_name)

    return prescription


def open_generated_docx(prescription):
    if not prescription.generated_docx:
        return None
    return prescription.generated_docx.open('rb')
