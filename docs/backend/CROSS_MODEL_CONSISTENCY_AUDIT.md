# Cross-Model Consistency Audit — Backend Business Integrity (PHASE B3)

Source of truth:
- `docs/backend/MODEL_RELATIONSHIP_GRAPH.md` (relationships + deletion behavior)
- `docs/backend/SERIALIZER_CONTRACT_AUDIT.md` (API-exposed serializer writable relationship inputs)
- Runtime tests executed inside the real Docker `web` container (see Validation evidence).

Goal: determine whether **type-valid** ORM/API writes can create **globally inconsistent business records** across models.

Important constraint: when the invariant intent cannot be derived confidently from the repository, the result is:
- **BUSINESS RULE UNDEFINED** (not a confirmed defect)

---

## Executive summary

### Confirmed behavior (as implemented)
The current backend **accepts inconsistent cross-model references** for several duplicated patient relationships:
- Payment can reference an invoice for Patient A while Payment.patient is Patient B (API accepted).
- Treatment can reference an appointment for Patient A while Treatment.patient is Patient B (API accepted).
- Treatment can reference a treatment plan for Patient A while Treatment.patient is Patient B (API accepted).
- Invoice can reference a treatment plan for Patient A while Invoice.patient is Patient B (API accepted).
- TreatmentPlanApproval can reference a plan for Patient A while approval.patient is Patient B (ORM accepted; approvals not exposed in API surface).

### Current enforcement level
Across audited paths, enforcement is typically:
- **DATABASE**: FK existence only; no cross-row equality constraints.
- **MODEL**: no `clean()` methods; no `save()` overrides.
- **SERIALIZER**: mostly `ModelSerializer(fields='__all__')` with no `validate()`.
- **VIEWSET/SERVICE/SIGNAL**: no evidence of extra checks for these invariants.

---

## Audited relationship paths (matrix)

Statuses:
- **PROTECTED**: invariant enforced
- **INCONSISTENCY ACCEPTED**: inconsistent state can be created
- **PARTIALLY PROTECTED**: some protection but bypass exists
- **BUSINESS RULE UNDEFINED**: intent not derivable from codebase
- **NOT APPLICABLE**: model path does not exist

| ID | Domain | Relationship path | Expected invariant | Derived from code | Current enforcement | ORM result | API result | Status | Risk | Evidence | Next audit phase |
|---|---|---|---|---|---|---|---|---|---|---|---|
| B3-001 | Billing | `Payment.invoice -> Invoice.patient` AND `Payment.patient` | `Payment.patient == Payment.invoice.patient` | Duplicate patient pointer exists; no comments/validation clarify intent (could allow 3rd-party payments) | NONE | Not tested | **Accepted** (201) with mismatch | **BUSINESS RULE UNDEFINED** (inconsistency accepted) | HIGH | `accounts/tests/test_cross_model_consistency.py::test_api_payment_patient_mismatch_with_invoice_patient_is_accepted` | B4/B13 |
| B3-002 | Billing | `Invoice.related_treatment_plan -> TreatmentPlan.patient` AND `Invoice.patient` | `Invoice.patient == related_treatment_plan.patient` | TreatmentPlan is patient-scoped; invoice also patient-scoped; no explicit rule implemented | NONE | Not tested | **Accepted** (201) with mismatch | **INCONSISTENCY ACCEPTED** | HIGH | `...::test_api_invoice_patient_mismatch_with_related_treatment_plan_patient_is_accepted` | B4/B13 |
| B3-003 | Clinical | `Treatment.appointment -> Appointment.patient` AND `Treatment.patient` | `Treatment.patient == Treatment.appointment.patient` | Appointment is explicitly patient-scoped; Treatment duplicates patient and also references appointment | NONE | Not tested | **Accepted** (201) with mismatch | **INCONSISTENCY ACCEPTED** | HIGH | `...::test_api_treatment_patient_mismatch_with_appointment_patient_is_accepted` | B4/B13 |
| B3-004 | Clinical | `Treatment.treatment_plan -> TreatmentPlan.patient` AND `Treatment.patient` | `Treatment.patient == TreatmentPlan.patient` | TreatmentPlan is explicitly patient-scoped; Treatment duplicates patient and also references plan | NONE | Not tested | **Accepted** (201) with mismatch | **INCONSISTENCY ACCEPTED** | HIGH | `...::test_api_treatment_patient_mismatch_with_treatment_plan_patient_is_accepted` | B4/B13 |
| B3-005 | Clinical | `TreatmentPlanApproval.treatment_plan.patient` AND `TreatmentPlanApproval.patient` | `Approval.patient == TreatmentPlan.patient` | Approval duplicates patient without any enforcement; approvals not exposed via ViewSet | NONE | **Accepted** with mismatch | N/A | **INCONSISTENCY ACCEPTED** | HIGH | `...::test_orm_treatment_plan_approval_patient_mismatch_with_plan_patient_is_accepted` | B4/B13 |

---

## Protected invariants / paths where inconsistency is structurally prevented

These are not necessarily *business rules*, but the model graph prevents certain classes of inconsistency:
- Imaging chain: `ImagingInstance -> ImagingSeries -> ImagingStudy -> Patient`.
  - Instances do not duplicate Patient, so you cannot directly attach an instance to the wrong patient *without moving the entire series/study*.
- Odontogram chain: `Tooth -> Odontogram -> Patient`.
  - Tooth does not duplicate Patient, so cross-patient mismatch cannot be expressed at the Tooth level.

---

## ORM vs API enforcement differences

Observed:
- For the audited paths, **API and ORM show the same lack of enforcement** (where API was applicable).
- For `TreatmentPlanApproval`, the inconsistency is **ORM-only** because approvals are not registered as an API resource in PHASE B0.

---

## Executable test inventory

Created tests (characterization tests asserting current behavior):
- `accounts/tests/test_cross_model_consistency.py`
  - `test_api_payment_patient_mismatch_with_invoice_patient_is_accepted`
  - `test_api_invoice_patient_mismatch_with_related_treatment_plan_patient_is_accepted`
  - `test_api_treatment_patient_mismatch_with_appointment_patient_is_accepted`
  - `test_api_treatment_patient_mismatch_with_treatment_plan_patient_is_accepted`
  - `test_orm_treatment_plan_approval_patient_mismatch_with_plan_patient_is_accepted`

---

## Findings to carry into PHASE B4 (business rules)

1. Decide whether the system intends to allow **third-party payments**.
   - If not allowed, enforce `Payment.patient == Payment.invoice.patient`.
   - If allowed, define semantics (payer vs beneficiary) and rename fields accordingly.
2. Treatment/Appointment/Plan patient consistency:
   - If treatments are always performed for the appointment’s patient, enforce patient equality.
3. Invoice/TreatmentPlan patient consistency:
   - If invoices are always for the plan’s patient, enforce equality.

Where intent is not explicitly defined in code:
- [WARN] BUSINESS RULE UNDEFINED

---

## Validation evidence

Commands executed in real runtime:
- `docker compose exec -T web python manage.py check`
- `docker compose exec -T web python manage.py test accounts.tests.test_cross_model_consistency`

Static validation:
- `PYTHONPYCACHEPREFIX=/tmp/pycache python3 -m compileall -q .`
