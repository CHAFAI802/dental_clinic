# State Machine Audit — Backend Business Integrity (PHASE B5)

Scope: find every real **status/state/phase/lifecycle** field and determine whether a **state machine** (allowed/forbidden transitions) is implemented.

Sources of truth:
- Models (`*/models.py`)
- API contract (`docs/backend/SERIALIZER_CONTRACT_AUDIT.md`)
- Business rules (`docs/backend/BUSINESS_RULE_MATRIX.md`)
- Cross-model tests (`accounts/tests/test_cross_model_consistency.py`)
- B5 characterization tests (`accounts/tests/test_state_machine_audit.py`)

Key rule: **CharField choices != state machine**.

---

## Executive summary

### Stateful fields discovered
- Total state-like fields inventoried: **29** across **17 models**.
- Only **1** field has defined choices at the Django model level:
  - `appointments.Appointment.status` (pending/confirmed/completed/cancelled/no_show)

### Transition/state machine implementation discovered
- **No explicit state machine implementation** was found (no `clean()`, no `save()` overrides, no transition services, no signals).
- All exposed `status` fields are writable via API (B2).
- **Appointment.status** is constrained only by DRF ChoiceField (API rejects invalid status) but:
  - **Any choice can be set from any other choice** (no transition policy)
  - ORM can save invalid values because Django choices are not DB-enforced.

Result for most models:
- **[WARN] STATE MACHINE UNDEFINED**

---

## Inventory of status/state fields

This inventory is derived from runtime model introspection in the Docker `web` container.

### Note on false positives
Fields ending with `_status` include some *data attributes* rather than workflow states:
- `patients.Patient.marital_status`
- `odontogram.Tooth.surface_status` (JSON)

They are included for completeness but are **NOT** treated as workflow state machines.

---

## State machine matrix

Columns:
- **MODEL**: Django model
- **FIELD**: exact field name
- **STATES**: explicit states/choices (if defined)
- **TRANSITION IMPLEMENTATION**: where transitions are enforced (if any)
- **ALLOWED TRANSITIONS / FORBIDDEN TRANSITIONS**: only if explicitly implemented
- **API BYPASS PATH / ORM BYPASS PATH**: how state can be set without transition checks
- **TEST EVIDENCE**: executable tests proving current behavior
- **STATUS**: `STATE MACHINE UNDEFINED | PARTIAL | IMPLEMENTED`
- **RISK**: integrity risk

| MODEL | FIELD | STATES | TRANSITION IMPLEMENTATION | ALLOWED TRANSITIONS | FORBIDDEN TRANSITIONS | API BYPASS PATH | ORM BYPASS PATH | TEST EVIDENCE | STATUS | RISK |
|---|---|---|---|---|---|---|---|---|---|---|
| `appointments.Appointment` | `status` | `pending/confirmed/completed/cancelled/no_show` (choices) | None found | [WARN] STATE MACHINE UNDEFINED | [WARN] STATE MACHINE UNDEFINED | `PATCH /api/appointments/{id}/` can set any choice directly | ORM can set any string; DB does not enforce choices | `test_api_appointment_status_can_jump_between_choices_and_does_not_log`; `test_orm_appointment_status_choices_not_enforced` | STATE MACHINE UNDEFINED | HIGH |
| `appointments.AppointmentStatusLog` | `previous_status` | none | None found | N/A | N/A | Not exposed | ORM direct writes | None | NOT APPLICABLE | LOW |
| `appointments.AppointmentStatusLog` | `new_status` | none | None found | N/A | N/A | Not exposed | ORM direct writes | None | NOT APPLICABLE | LOW |
| `treatments.Treatment` | `status` | none (free text) | None found | [WARN] STATE MACHINE UNDEFINED | [WARN] STATE MACHINE UNDEFINED | `PATCH /api/treatments/{id}/` accepts arbitrary string | ORM accepts arbitrary string | `test_api_treatment_status_accepts_arbitrary_values` | STATE MACHINE UNDEFINED | HIGH |
| `treatment_plans.TreatmentPlan` | `status` | none (free text) | None found | [WARN] STATE MACHINE UNDEFINED | [WARN] STATE MACHINE UNDEFINED | `PATCH /api/treatment-plans/{id}/` accepts arbitrary string | ORM accepts arbitrary string | (covered indirectly by B3 tests; no B5-specific) | STATE MACHINE UNDEFINED | HIGH |
| `treatment_plans.TreatmentPlanStage` | `status` | none (free text) | None found | [WARN] STATE MACHINE UNDEFINED | [WARN] STATE MACHINE UNDEFINED | Not exposed | ORM accepts arbitrary string | None | STATE MACHINE UNDEFINED | MEDIUM |
| `prescriptions.Prescription` | `status` | none (free text) | None found | [WARN] STATE MACHINE UNDEFINED | [WARN] STATE MACHINE UNDEFINED | `PATCH /api/prescriptions/{id}/` accepts arbitrary string | ORM accepts arbitrary string | (not tested in B5) | STATE MACHINE UNDEFINED | HIGH |
| `billing.Invoice` | `status` | none (free text) | None found | [WARN] STATE MACHINE UNDEFINED | [WARN] STATE MACHINE UNDEFINED | `PATCH /api/invoices/{id}/` accepts arbitrary string | ORM accepts arbitrary string | `test_api_invoice_status_accepts_arbitrary_values` | STATE MACHINE UNDEFINED | HIGH |
| `billing.Payment` | `status` | none (free text) | None found | [WARN] STATE MACHINE UNDEFINED | [WARN] STATE MACHINE UNDEFINED | `PATCH /api/payments/{id}/` accepts arbitrary string | ORM accepts arbitrary string | `test_api_payment_status_accepts_arbitrary_values` | STATE MACHINE UNDEFINED | HIGH |
| `billing.Estimate` | `status` | none (free text) | None found | [WARN] STATE MACHINE UNDEFINED | [WARN] STATE MACHINE UNDEFINED | Not exposed | ORM accepts arbitrary string | None | STATE MACHINE UNDEFINED | MEDIUM |
| `billing.CreditNote` | `status` | none (free text) | None found | [WARN] STATE MACHINE UNDEFINED | [WARN] STATE MACHINE UNDEFINED | Not exposed | ORM accepts arbitrary string | None | STATE MACHINE UNDEFINED | MEDIUM |
| `documents.Document` | `status` | none (free text) | None found | [WARN] STATE MACHINE UNDEFINED | [WARN] STATE MACHINE UNDEFINED | `PATCH /api/documents/{id}/` accepts arbitrary string | ORM accepts arbitrary string | `test_api_document_status_accepts_arbitrary_values` | STATE MACHINE UNDEFINED | HIGH |
| `documents.ConsentForm` | `status` | none (free text) | None found | [WARN] STATE MACHINE UNDEFINED | [WARN] STATE MACHINE UNDEFINED | Not exposed | ORM accepts arbitrary string | None | STATE MACHINE UNDEFINED | MEDIUM |
| `notifications.Notification` | `status` | none (free text) | None found | [WARN] STATE MACHINE UNDEFINED | [WARN] STATE MACHINE UNDEFINED | `PATCH /api/notifications/{id}/` accepts arbitrary string | ORM accepts arbitrary string | `test_api_notification_status_accepts_arbitrary_values` | STATE MACHINE UNDEFINED | HIGH |
| `notifications.NotificationLog` | `status` | none | None found | N/A | N/A | Not exposed | ORM accepts arbitrary string | None | NOT APPLICABLE | LOW |
| `notifications.NotificationEvent` | `status` | none | None found | N/A | N/A | Not exposed | ORM accepts arbitrary string | None | NOT APPLICABLE | LOW |
| `imaging.ImagingStudy` | `status` | none (free text) | None found | [WARN] STATE MACHINE UNDEFINED | [WARN] STATE MACHINE UNDEFINED | `PATCH /api/imaging-studies/{id}/` accepts arbitrary string | ORM accepts arbitrary string | `test_api_imaging_study_status_accepts_arbitrary_values` | STATE MACHINE UNDEFINED | HIGH |
| `imaging.ImagingReport` | `status` | none | None found | [WARN] STATE MACHINE UNDEFINED | [WARN] STATE MACHINE UNDEFINED | Not exposed | ORM accepts arbitrary string | None | STATE MACHINE UNDEFINED | MEDIUM |
| `reports.ReportExecution` | `status` | none | None found | [WARN] STATE MACHINE UNDEFINED | [WARN] STATE MACHINE UNDEFINED | Not exposed | ORM accepts arbitrary string | None | STATE MACHINE UNDEFINED | LOW |
| `staff.StaffProfile` | `status` | none | None found | [WARN] STATE MACHINE UNDEFINED | [WARN] STATE MACHINE UNDEFINED | `PATCH /api/staff/{id}/` accepts arbitrary string | ORM accepts arbitrary string | (not tested in B5) | STATE MACHINE UNDEFINED | MEDIUM |
| `staff.Contract` | `status` | none | None found | [WARN] STATE MACHINE UNDEFINED | [WARN] STATE MACHINE UNDEFINED | Not exposed | ORM accepts arbitrary string | None | STATE MACHINE UNDEFINED | LOW |
| `staff.AttendanceRecord` | `status` | none | None found | [WARN] STATE MACHINE UNDEFINED | [WARN] STATE MACHINE UNDEFINED | Not exposed | ORM accepts arbitrary string | None | STATE MACHINE UNDEFINED | LOW |
| `staff.LeaveRequest` | `status` | none | None found | [WARN] STATE MACHINE UNDEFINED | [WARN] STATE MACHINE UNDEFINED | Not exposed | ORM accepts arbitrary string | None | STATE MACHINE UNDEFINED | LOW |
| `patients.MedicalHistory` | `status` | none | None found | [WARN] STATE MACHINE UNDEFINED | [WARN] STATE MACHINE UNDEFINED | Not exposed | ORM accepts arbitrary string | None | STATE MACHINE UNDEFINED | LOW |
| `patients.PatientConsent` | `status` | none | None found | [WARN] STATE MACHINE UNDEFINED | [WARN] STATE MACHINE UNDEFINED | Not exposed | ORM accepts arbitrary string | None | STATE MACHINE UNDEFINED | LOW |
| `odontogram.Tooth` | `status` | none | None found | [WARN] STATE MACHINE UNDEFINED | [WARN] STATE MACHINE UNDEFINED | `PATCH /api/teeth/{id}/` accepts arbitrary string | ORM accepts arbitrary string | (not tested in B5) | STATE MACHINE UNDEFINED | MEDIUM |
| `odontogram.ToothTreatment` | `status` | none | None found | [WARN] STATE MACHINE UNDEFINED | [WARN] STATE MACHINE UNDEFINED | Not exposed | ORM accepts arbitrary string | None | STATE MACHINE UNDEFINED | LOW |
| `patients.Patient` | `marital_status` | none | N/A (data attribute) | N/A | N/A | API accepts arbitrary string | ORM accepts arbitrary string | None | NOT APPLICABLE | INFO |
| `odontogram.Tooth` | `surface_status` (JSON) | N/A | N/A (data attribute) | N/A | N/A | API accepts JSON | ORM accepts JSON | None | NOT APPLICABLE | INFO |

---

## Validation evidence

Commands executed are recorded in the roadmap Execution Journal for PHASE B5.
