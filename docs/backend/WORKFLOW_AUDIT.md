# END-TO-END BUSINESS WORKFLOW AUDIT

## Status

PHASE B12 characterization complete.

Validation status: **PASS with WARN**

---

## Scope

This audit characterizes the current end-to-end business workflow graph across:

- patients
- appointments
- treatment plans
- treatments
- billing

The objective is to verify whether the current backend can persist a complete clinical-to-financial workflow and to identify cross-domain integrity gaps.

---

## Characterized workflow

The principal business workflow is:

Patient
→ Appointment
→ Treatment Plan
→ Treatment
→ Invoice
→ Invoice Line
→ Payment

The current model graph allows this complete workflow to be persisted successfully.

No orchestration service is required by the ORM to construct the workflow.

---

## Verified behavior

### Complete clinical-to-financial workflow

A complete workflow can be persisted across the current domain models.

The backend supports creation of:

1. a patient;
2. an appointment;
3. a treatment plan;
4. a treatment;
5. an invoice;
6. an invoice line;
7. a payment.

The relationships remain queryable after persistence.

Status: **VERIFIED**

---

## Cross-domain integrity findings

### Treatment and appointment patient consistency

A `Treatment` can reference an `Appointment` belonging to another patient.

No model-level constraint currently verifies:

`Treatment.patient == Treatment.appointment.patient`

Status: **WARN**

Risk:

Clinical treatment data can be attached to an appointment from an unrelated patient.

---

### Treatment and treatment-plan patient consistency

A `Treatment` can reference a `TreatmentPlan` belonging to another patient.

No model-level constraint currently verifies:

`Treatment.patient == Treatment.treatment_plan.patient`

Status: **WARN**

Risk:

A treatment can be persisted under a treatment plan owned by another patient.

---

### Invoice-line treatment patient consistency

An `InvoiceLine` can reference a `Treatment` belonging to a patient different from the invoice patient.

No model-level constraint currently verifies:

`InvoiceLine.invoice.patient == InvoiceLine.treatment.patient`

Status: **WARN**

Risk:

Clinical services from one patient can be financially attached to another patient's invoice.

---

### Payment and invoice patient consistency

A `Payment` can reference an `Invoice` belonging to another patient.

No model-level constraint currently verifies:

`Payment.patient == Payment.invoice.patient`

Status: **WARN**

Risk:

A payment can be persisted against the financial account of an unrelated patient.

---

## Financial balance behavior

Creating a `Payment` does not automatically update invoice balance fields.

Payment persistence and invoice financial state are independent write operations.

Status: **WARN**

Risk:

Invoice totals, paid amounts, and remaining balances can diverge from persisted payment records unless application code explicitly synchronizes them.

---

## Workflow orchestration finding

The current backend exposes a connected relational graph but does not define a single transactional workflow service for the complete clinical-to-financial lifecycle.

The ORM permits individual domain records to be created independently.

Status: **WARN**

Consequences:

- partial workflows can exist;
- cross-patient references can be persisted;
- financial state synchronization depends on caller behavior;
- multi-model workflow atomicity is not globally guaranteed.

---

## Characterization tests

Executable characterization coverage is implemented in:

`accounts/tests/test_end_to_end_business_workflows.py`

The suite contains six deterministic workflow tests.

Verified characteristics include:

- complete clinical-to-financial workflow persistence;
- treatment/appointment patient mismatch acceptance;
- treatment/treatment-plan patient mismatch acceptance;
- invoice-line/treatment patient mismatch acceptance;
- payment/invoice patient mismatch acceptance;
- absence of automatic invoice balance synchronization after payment creation.

---

## Validation

The following validation commands pass:

`python manage.py test accounts.tests.test_end_to_end_business_workflows`

Result:

- 6 tests discovered;
- 6 tests passed.

Additional validation:

- `python manage.py check` — PASS
- static `compileall` — PASS
- `git diff --check` — PASS

---

## Final assessment

The current backend can persist the principal clinical-to-financial workflow.

However, the workflow graph is relationally connected without sufficient business-level consistency enforcement.

The most important remediation targets are:

1. enforce patient consistency between treatment and appointment;
2. enforce patient consistency between treatment and treatment plan;
3. enforce patient consistency between invoice lines and referenced treatments;
4. enforce patient consistency between payments and invoices;
5. centralize payment-to-invoice balance synchronization;
6. define transactional orchestration boundaries for critical multi-model workflows.

These findings must be carried into PHASE B13 — REMEDIATION PLAN.
