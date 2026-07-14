# Serializer Contract Audit — Backend Business Integrity (PHASE B2)

Source of truth (routing chain):
- `dental_clinic/urls.py` includes each app router under `/api/`.
- Each app `urls.py` registers DRF `DefaultRouter()` ViewSets.
- ViewSets declare `serializer_class` directly (no `get_serializer_class()` overrides found).
- Runtime confirmation done via `docker compose exec web python manage.py shell -c ...` introspection of resolver → viewset → serializer.

This document audits **only serializers actually used by exposed API operations**.

---

## Executive summary

### What exists
- **22 exposed ViewSets** (from PHASE B0 baseline), each binding exactly **1 serializer_class**.
- **22 exposed serializers audited**.
- Serializer implementations are mostly `ModelSerializer` with `fields = '__all__'`.

### Key integrity risks (derived from current serializer implementations)
Severity levels are audit-only and refer to *backend business integrity* risk.

**CRITICAL / HIGH**
1. **Mass-assignment exposure**: `fields='__all__'` makes many backend-controlled fields writable (examples):
   - `SoftDeleteModel` flags (`is_deleted`, `deleted_at`) are writable on `Patient`, `Appointment`, `Odontogram`, `Tooth`, `Treatment`, `TreatmentPlan`.
   - Attribution/ownership fields writable: `created_by`, `confirmed_by`, `cancelled_by`, `paid_by`, etc.
   - Financial totals writable: `Invoice.total_amount`, `Invoice.paid_amount`, `Invoice.balance_due`.
2. **Missing cross-model validation**:
   - `PaymentSerializer` allows `patient` independent of `invoice.patient` (B1 finding).
   - Many serializers accept foreign keys by raw PK (PrimaryKeyRelatedField) with no additional consistency checks.
3. **Status/state fields are writable with no transition validation at serializer level** across multiple domains (`Appointment.status`, `Treatment.status`, `Invoice.status`, `Payment.status`, etc.).

**MEDIUM**
4. **FileField uploads have no serializer-level validation** (type/size/content/extension) for:
   - `ImagingInstance.file` and `.thumbnail`
   - `Document.pdf_file`, `Prescription.pdf_file`

**WARN**
5. `AuditLogSerializer` is fully writable (except auto fields) even though the API exposes it via a **read-only viewset**; if reused elsewhere for writes, it would be unsafe.
6. `LoginView` parses request data manually (no serializer), so the request contract is only loosely validated.

---

## Exposed ViewSets and serializer inventory (22/22)

Derived from `*/urls.py` router registrations + runtime URL resolver introspection.

| ViewSet | Endpoint (router prefix) | Serializer | Model |
|---|---|---|---|
| `UserViewSet` | `/api/users/` | `accounts.serializers.UserSerializer` | `accounts.User` |
| `AuditLogViewSet` (read-only) | `/api/audit-logs/` | `accounts.serializers.AuditLogSerializer` | `accounts.AuditLog` |
| `PatientViewSet` | `/api/patients/` | `patients.serializers.PatientSerializer` | `patients.Patient` |
| `RoomViewSet` | `/api/rooms/` | `appointments.serializers.RoomSerializer` | `appointments.Room` |
| `AppointmentViewSet` | `/api/appointments/` | `appointments.serializers.AppointmentSerializer` | `appointments.Appointment` |
| `OdontogramViewSet` | `/api/odontograms/` | `odontogram.serializers.OdontogramSerializer` | `odontogram.Odontogram` |
| `ToothViewSet` | `/api/teeth/` | `odontogram.serializers.ToothSerializer` | `odontogram.Tooth` |
| `TreatmentPlanViewSet` | `/api/treatment-plans/` | `treatment_plans.serializers.TreatmentPlanSerializer` | `treatment_plans.TreatmentPlan` |
| `TreatmentViewSet` | `/api/treatments/` | `treatments.serializers.TreatmentSerializer` | `treatments.Treatment` |
| `PrescriptionTemplateViewSet` | `/api/prescription-templates/` | `prescriptions.serializers.PrescriptionTemplateSerializer` | `prescriptions.PrescriptionTemplate` |
| `PrescriptionViewSet` | `/api/prescriptions/` | `prescriptions.serializers.PrescriptionSerializer` | `prescriptions.Prescription` |
| `InvoiceViewSet` | `/api/invoices/` | `billing.serializers.InvoiceSerializer` | `billing.Invoice` |
| `PaymentViewSet` | `/api/payments/` | `billing.serializers.PaymentSerializer` | `billing.Payment` |
| `DocumentTemplateViewSet` | `/api/document-templates/` | `documents.serializers.DocumentTemplateSerializer` | `documents.DocumentTemplate` |
| `DocumentViewSet` | `/api/documents/` | `documents.serializers.DocumentSerializer` | `documents.Document` |
| `InventoryItemViewSet` | `/api/inventory-items/` | `inventory.serializers.InventoryItemSerializer` | `inventory.InventoryItem` |
| `StaffProfileViewSet` | `/api/staff/` | `staff.serializers.StaffProfileSerializer` | `staff.StaffProfile` |
| `ReportDefinitionViewSet` | `/api/reports/` | `reports.serializers.ReportDefinitionSerializer` | `reports.ReportDefinition` |
| `NotificationTemplateViewSet` | `/api/notification-templates/` | `notifications.serializers.NotificationTemplateSerializer` | `notifications.NotificationTemplate` |
| `NotificationViewSet` | `/api/notifications/` | `notifications.serializers.NotificationSerializer` | `notifications.Notification` |
| `ImagingStudyViewSet` | `/api/imaging-studies/` | `imaging.serializers.ImagingStudySerializer` | `imaging.ImagingStudy` |
| `ImagingInstanceViewSet` | `/api/imaging-instances/` | `imaging.serializers.ImagingInstanceSerializer` | `imaging.ImagingInstance` |

---

## Serializer contract matrix (field-level summary)

Definitions:
- **Readable fields**: all serializer fields, including read-only.
- **Writable fields**: all fields except `read_only_fields` and `write_only_fields` restrictions.
- For serializers using `fields='__all__'`, "readable" is effectively all model fields (plus any explicitly added serializer fields).

> Runtime evidence for required/read-only/write-only fields was collected in the container; see **Validation evidence**.

| Serializer | Model | API resource | Readable fields | Writable fields | Required fields | Optional fields | Read-only fields | Write-only fields | Validation rules | Relationship inputs | Risks | Status |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| `UserSerializer` | `User` | `/api/users/` and auth responses | Explicit list (10 fields) | All except `id`; `password` write-only | `email, first_name, last_name, role` | `phone, timezone, language, is_active, password*` | `id` | `password` | `validate_email` lowercases; `validate_password` non-empty; `create()` requires password; `update()` sets password if provided | none | **Model/serializer requiredness mismatch**: password `required=False` but create requires it. No protection against setting `is_active` etc beyond permissions. | Audited |
| `AuditLogSerializer` | `AuditLog` | `/api/audit-logs/` (read-only ViewSet) | `__all__` (11) | **All non-auto fields writable** | `action, model_name` | others optional | `id, created_at, updated_at` | none | No custom validation | `user` PK | ViewSet is read-only, but serializer itself would allow mass-assignment if reused. Also `object_id` is UUIDField (B1 risk). | Audited |
| `PatientSerializer` | `Patient` | `/api/patients/` | `__all__` (40) | All except auto `id/created_at/updated_at` | `first_name, last_name, birthdate, gender, phone` | many optional | `id, created_at, updated_at` | none | No custom validation | none | **Soft-delete flags writable** (`is_deleted`, `deleted_at`). No validation for formats beyond DRF types. | Audited |
| `RoomSerializer` | `Room` | `/api/rooms/` | `__all__` (6) | All except `id` | `name` | others optional | `id` | none | No custom validation | none | `is_active` is writable; ViewSet filters `is_active=True` but serializer allows setting false. | Audited |
| `AppointmentSerializer` | `Appointment` | `/api/appointments/` | `__all__` (22) | All except auto fields | `start_at, end_at, patient, practitioner` | others optional | `id, created_at, updated_at` | none | No custom validation | many FK PKs (`patient`, `practitioner`, etc.) | **Soft-delete writable**; **status writable**; **confirmed/cancel fields writable**; no validation for `end_at > start_at` or overlap constraints. | Audited |
| `OdontogramSerializer` | `Odontogram` | `/api/odontograms/` | `__all__` + `teeth` nested read-only (10 total) | All except auto fields and `teeth` | `patient` | others optional | `id, teeth, created_at, updated_at` | none | No custom validation | `patient`, `created_by` PK | `created_by` writable; `version` writable; soft-delete writable. Nested teeth is read-only (safe). | Audited |
| `ToothSerializer` | `Tooth` | `/api/teeth/` | `__all__` (12) | All except auto fields | `number, type, status, odontogram` | others optional | `id, created_at, updated_at` | none | Default ModelSerializer validators apply (includes UniqueTogetherValidator for (`odontogram`,`number`)) | `odontogram` PK | Soft-delete writable; free-text status/type (no choices in model). | Audited |
| `TreatmentPlanSerializer` | `TreatmentPlan` | `/api/treatment-plans/` | `__all__` (13) | All except auto fields | `status, patient` | others optional | `id, created_at, updated_at` | none | No custom validation | `patient`, `created_by` PK | **Soft-delete writable**; totals writable; `patient_approved_at` writable; no validation. | Audited |
| `TreatmentSerializer` | `Treatment` | `/api/treatments/` | `__all__` (22) | All except auto fields | `status, category, code, label, patient, dentist` | others optional | `id, created_at, updated_at` | none | No custom validation | multiple FK PKs | **Soft-delete writable**; monetary totals writable; links to appointment/plan writable w/o consistency checks. | Audited |
| `PrescriptionTemplateSerializer` | `PrescriptionTemplate` | `/api/prescription-templates/` | `__all__` (8) | All except auto fields | `name, content` | others optional | `id, created_at, updated_at` | none | No custom validation | none | `variables` JSON not validated; `is_active` writable. | Audited |
| `PrescriptionSerializer` | `Prescription` | `/api/prescriptions/` | `__all__` (11) | All except auto fields | `status, patient, dentist, template` | others optional | `id, created_at, updated_at` | none | No custom validation | PK FKs | `generated_at` writable; `pdf_file` upload unvalidated; no check that `filled_data` matches template variable definitions. | Audited |
| `InvoiceSerializer` | `Invoice` | `/api/invoices/` | `__all__` (16) | All except auto fields | `issued_at, due_date, status, reference_number, patient` | others optional | `id, created_at, updated_at` | none | No custom validation | PK FKs | **Financial integrity risk:** totals and balances writable; no non-negative checks; no state rules. | Audited |
| `PaymentSerializer` | `Payment` | `/api/payments/` | `__all__` (11) | All except auto fields | `payment_at, amount, method, status, invoice, patient` | others optional | `id, created_at, updated_at` | none | No custom validation | PK FKs | **B1 traced:** allows `patient` != `invoice.patient`. No validation for amount <= balance, non-negative, etc. | Audited |
| `DocumentTemplateSerializer` | `DocumentTemplate` | `/api/document-templates/` | `__all__` (9) | All except auto fields | `name, content` | others optional | `id, created_at, updated_at` | none | No custom validation | none | `variables` JSON not validated; `is_active` writable. | Audited |
| `DocumentSerializer` | `Document` | `/api/documents/` | `__all__` (12) | All except auto fields | `document_type, title, content, status, patient` | others optional | `id, created_at, updated_at` | none | No custom validation | PK FKs | `created_by` writable; `signed_at` writable; `pdf_file` upload unvalidated. | Audited |
| `InventoryItemSerializer` | `InventoryItem` | `/api/inventory-items/` | `__all__` (14) | All except auto fields | `sku, name, unit` | others optional | `id, created_at, updated_at` | none | No custom validation | `category` PK | No checks preventing negative `stock_quantity`, etc. | Audited |
| `StaffProfileSerializer` | `StaffProfile` | `/api/staff/` | `__all__` (15) | All except auto fields | `employee_number, hire_date, department, job_title, employment_type, status, user` | others optional | `id, created_at, updated_at` | none | No custom validation | `user`, `manager` PK | `user` assignment writable (mass assignment). No validation for status enum (free text). | Audited |
| `ReportDefinitionSerializer` | `ReportDefinition` | `/api/reports/` | `__all__` (9) | All except auto fields | `name, query_type` | others optional | `id, created_at, updated_at` | none | No custom validation | none | `is_public` writable; query params/templating JSON not validated. | Audited |
| `NotificationTemplateSerializer` | `NotificationTemplate` | `/api/notification-templates/` | `__all__` (10) | All except auto fields | `name, channel, body` | others optional | `id, created_at, updated_at` | none | No custom validation | none | Template content/variables JSON not validated. | Audited |
| `NotificationSerializer` | `Notification` | `/api/notifications/` | `__all__` (11) | All except auto fields | `channel, status` | others optional | `id, created_at, updated_at` | none | No custom validation | optional recipient PK FKs | No validation requiring at least one recipient; `sent_at` and `error_message` writable. | Audited |
| `ImagingStudySerializer` | `ImagingStudy` | `/api/imaging-studies/` | `__all__` (10) | All except auto fields | `study_type, study_date, status, patient, practitioner` | others optional | `id, created_at, updated_at` | none | No custom validation | PK FKs | Status writable, no constraints; no validation of dates. | Audited |
| `ImagingInstanceSerializer` | `ImagingInstance` | `/api/imaging-instances/` | `__all__` (8) | All except `id` | `instance_number, file, file_type, study_date, series` | others optional | `id` | none | No custom validation | `series` PK | **File upload risk:** no validation of MIME, extension, file size; `file_type` is client-provided string. | Audited |

---

## Model/serializer mismatch findings

1. **User password requiredness**
- Serializer declares `password` as `required=False`, but `create()` raises if password missing.
- Impact: request contract differs from serializer schema; API clients may think password optional.

2. **Soft-delete fields exposed as writable** (B1 traced)
- `Patient/Appointment/Odontogram/Tooth/TreatmentPlan/Treatment` inherit `SoftDeleteModel`.
- Their serializers are `fields='__all__'` → `is_deleted`, `deleted_at` are writable.
- ViewSets filter `is_deleted=False`, but do not prevent clients from setting `is_deleted=True` on update.

---

## Unsafe writable field findings (mass assignment)

The following categories are writable in serializers without explicit restriction:

### Attribution / audit-like fields (should typically be server-controlled)
- `Appointment.created_by`, `confirmed_by`, `cancelled_by`, and timestamps `confirmed_at`, `cancelled_at`.
- `TreatmentPlan.created_by`.
- `Document.created_by`.
- `Payment.paid_by`.

**Status:** [WARN] BUSINESS RULE UNDEFINED (no server-side enforcement found in serializers).

### Calculated or aggregate financial fields
- `Invoice.total_amount`, `tax_amount`, `paid_amount`, `balance_due` are writable.
- No serializer validation enforces non-negativity or consistency.

### File fields
- `Document.pdf_file`, `Prescription.pdf_file`, `ImagingInstance.file`, `ImagingInstance.thumbnail` are writable with no serializer-level validation.

---

## Missing validation findings (type vs business validation)

DRF type validation exists (dates/decimals/fk ids), but **business validation is largely absent** at serializer level:
- No validation that appointment `end_at > start_at`.
- No overlap/availability validation for rooms/practitioners.
- No non-negative money constraints.
- No check that `Payment.amount` does not exceed invoice balance.
- No check that `Payment.patient` equals `Payment.invoice.patient` (B1 traced).
- No state transition validation despite multiple status fields.

Where intended rules cannot be derived from code:
- **[WARN] BUSINESS RULE UNDEFINED**

---

## Cross-model validation coverage (B1 findings traced)

### B1: `Payment.patient` vs `Invoice.patient`
- Serializer behavior: both are writable PrimaryKeyRelatedFields.
- Validation: **none** (no `validate()` override, no field validators).
- Database: **no constraint**.
- Risk: type-valid API requests can create globally inconsistent billing data.

### B1: `TreatmentPlanApproval.patient` vs `TreatmentPlan.patient`
- Not directly exposed by API in PHASE B0 surface (no ViewSet registered for approvals).
- Therefore: not covered in B2 serializer contract (to be tested in B3 if any write path exists elsewhere).

---

## Authentication request/response contract

### `POST /api/auth/login/`
- Request parsing: manual (`request.data.get('email')`, `request.data.get('password')`).
- No request serializer.
- Validation:
  - Returns 400 if email or password missing.
  - Delegates credential validation to `accounts.services.authentication.login_with_token`.
- Response includes:
  - `token` (DRF token key)
  - `user` serialized with `UserSerializer`
  - `role_label`
  - `accessible_modules`

### `GET /api/auth/me/`
- Response includes same `user` payload via `UserSerializer`.

### `POST /api/auth/logout/`
- No serializer; deletes Token rows for request.user.

---

## Findings to carry into PHASE B3 (cross-model consistency)

The serializer contract allows the following *type-valid* but potentially inconsistent combinations:
- `Payment(invoice=X, patient=Y)` where `Y != X.patient`.
- `Treatment(patient=A, appointment=B)` where `B.patient != A` (no serializer validation).
- `Treatment(patient=A, treatment_plan=P)` where `P.patient != A`.
- `Document(patient=A, template=T)` (template not tied to patient; probably OK) but `created_by` arbitrary.
- `Appointment(patient=A, practitioner=U, room=R)` no checks for overlaps.

These will be turned into executable inconsistency tests in PHASE B3 **without inventing business rules**.

---

## Validation evidence

Commands executed (runtime preferred, using the real `web` container):
- `docker compose exec -T web python manage.py check` → PASS (0 issues)
- `docker compose exec -T web python manage.py shell -c "..."` → PASS (resolved all 22 viewsets and extracted serializer required/read-only/write-only + relationship fields)

Static syntax validation:
- `PYTHONPYCACHEPREFIX=/tmp/pycache python3 -m compileall -q .` → PASS

---

## Status

PHASE B2 audit completed (documentation-only, no behavioral changes applied).
