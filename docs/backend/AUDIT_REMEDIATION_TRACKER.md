# BACKEND AUDIT REMEDIATION TRACKER

## Status

This document tracks the remediation lifecycle of verified backend integrity findings identified during PHASE B0 through PHASE B12 and consolidated during PHASE B13.

It provides stable finding identifiers and links each verified finding to its remediation phase, implementation status, validation evidence, and backend contract freeze readiness.

This tracker does not redefine audit findings or introduce new business requirements.

## Scope

The tracker covers verified findings from:

- MODEL_RELATIONSHIP_GRAPH.md
- SERIALIZER_CONTRACT_AUDIT.md
- CROSS_MODEL_CONSISTENCY_AUDIT.md
- BUSINESS_RULE_MATRIX.md
- STATE_MACHINE_AUDIT.md
- AUTHORIZATION_MATRIX.md
- CONCURRENCY_AUDIT.md
- IDEMPOTENCE_AUDIT.md
- FILE_INTEGRITY_AUDIT.md
- AUDIT_TRAIL_AUDIT.md
- WEBSITE_DOMAIN_SPECIFICATION.md
- WORKFLOW_AUDIT.md
- BACKEND_BUSINESS_INTEGRITY_REMEDIATION_PLAN.md
- SECURITY_AUDIT.md

## Tracker Rules

Each verified finding receives one stable identifier.

Stable identifiers must not change when:

- remediation priority changes,
- implementation moves between commits,
- additional tests are added,
- remediation status changes.

An existing finding must reuse its identifier when confirmed by multiple audit phases.

New identifiers must only be introduced when supported by verified audit evidence.

The tracker does not mark a finding as resolved solely because implementation code exists.

Resolution requires recorded validation evidence.

## Identifier Domains

| Prefix | Domain |
|---|---|
| DEL | Deletion and retention |
| SER | Serializer and API write contract |
| CONS | Cross-model consistency |
| BILL | Billing and financial integrity |
| SCHED | Scheduling |
| INV | Inventory |
| STATE | State machines |
| AUTH | Authorization |
| CONC | Concurrency and transaction safety |
| IDEM | Idempotence and duplicate submission |
| FILE | File integrity and lifecycle |
| AUD | Audit trail integrity |
| WEB | Website domain |
| SEC | Security configuration and operational hardening |
| WF | Workflow orchestration |
| POL | Policy-dependent findings |

## Status Definitions

| Status | Meaning |
|---|---|
| OPEN | Verified finding; remediation not started |
| IN_PROGRESS | Remediation implementation is active |
| IMPLEMENTED | Code changes exist but validation is incomplete |
| VALIDATED | Remediation has passed its required validation strategy |
| BLOCKED | Remediation cannot proceed because a dependency is unresolved |
| DEFERRED_DECISION | Explicit product or domain decision is required |
| ACCEPTED_RISK | Risk explicitly accepted and documented |
| FROZEN | Validated finding incorporated into the B14 backend contract freeze |

## Remediation Phase Mapping

| Phase | Objective |
|---|---|
| R1 | Deletion and data-retention integrity |
| R2 | Serializer ownership and write-contract hardening |
| R3 | Cross-model consistency |
| R4 | Business rule enforcement |
| R5 | State machine enforcement |
| R7 | Authorization scope |
| R8 | File integrity and lifecycle |
| R9 | Audit trail completeness |
| R10 | Asynchronous and idempotent workflow hardening |
| R11 | Security hardening |
## Master Finding Index

| ID | Domain | Finding | Audit Evidence | Priority | Remediation Phase | Status |
|---|---|---|---|---|---|---|
| DEL-001 | Deletion and retention | SoftDeleteModel does not implement soft deletion; Model.delete() still performs hard deletion and can trigger CASCADE chains. | MODEL_RELATIONSHIP_GRAPH.md — B1.C, B1.F | P0 | R1 | OPEN |
| DEL-002 | Deletion and retention | Patient hard deletion cascades across clinical, billing, imaging, and document history. | MODEL_RELATIONSHIP_GRAPH.md — B1.D, B1.F | P0 | R1 | OPEN |
| DEL-003 | Deletion and retention | Invoice deletion cascades to payments and credit notes, allowing financial history loss. | MODEL_RELATIONSHIP_GRAPH.md — B1.D, B1.F | P0 | R1 | OPEN |
| SER-001 | Serializer and API write contract | ModelSerializer fields='__all__' exposes backend-controlled fields through broad writable API contracts. | SERIALIZER_CONTRACT_AUDIT.md — Executive summary, Unsafe writable field findings | P1 | R2 | OPEN |
| SER-002 | Serializer and API write contract | Soft-delete fields is_deleted and deleted_at are client-writable on exposed soft-deletable resources. | SERIALIZER_CONTRACT_AUDIT.md — Model/serializer mismatch findings | P1 | R2 | OPEN |
| SER-003 | Serializer and API write contract | Attribution and workflow audit-like fields are client-writable without server-side ownership enforcement. | SERIALIZER_CONTRACT_AUDIT.md — Unsafe writable field findings | P1 | R2 | OPEN |
| SER-004 | Serializer and API write contract | User password is declared optional by the serializer contract but create() requires it; API user creation and password update also lack evidenced Django password-validator enforcement. | SERIALIZER_CONTRACT_AUDIT.md — Model/serializer mismatch findings; SECURITY_AUDIT.md — SEC-007 | P1 | R2 | OPEN |
| SER-005 | Serializer and API write contract | AuditLogSerializer is writable by contract although current API exposure is read-only. | SERIALIZER_CONTRACT_AUDIT.md — Executive summary | P2 | R2 | OPEN |
| SER-006 | Serializer and API write contract | Login request data is manually parsed without a serializer-defined request contract. | SERIALIZER_CONTRACT_AUDIT.md — Executive summary, Authentication request/response contract | P2 | R2 | OPEN |
| SER-007 | Serializer and API write contract | New or modified domain records can reference soft-deleted patients because patient lifecycle eligibility is not enforced at writable API boundaries. | domain_coherence/G2_COHERENCE_TRACKER.md — G2-F17, G2-F21, G2-F28, G2-C8-F6, G2-C9-F8, G2-CHECK-09, G2-CHECK-10, G2-CHECK-11 | P1 | R2 | OPEN |
| CONS-001 | Cross-model consistency | Invoice.patient can differ from the patient of its related treatment plan. | CROSS_MODEL_CONSISTENCY_AUDIT.md — B3-002 | P1 | R3 | OPEN |
| CONS-002 | Cross-model consistency | Treatment.patient can differ from the patient of its referenced appointment. | CROSS_MODEL_CONSISTENCY_AUDIT.md — B3-003 | P1 | R3 | OPEN |
| CONS-003 | Cross-model consistency | Treatment.patient can differ from the patient of its referenced treatment plan. | CROSS_MODEL_CONSISTENCY_AUDIT.md — B3-004 | P1 | R3 | OPEN |
| CONS-004 | Cross-model consistency | TreatmentPlanApproval.patient can differ from the patient of its treatment plan. | CROSS_MODEL_CONSISTENCY_AUDIT.md — B3-005 | P1 | R3 | OPEN |
| CONS-005 | Cross-model consistency | DocumentAttachment.patient can differ from the patient of its related document. | domain_coherence/G2_COHERENCE_TRACKER.md — G2-CHECK-11, Cross-Patient Attachment Inconsistency | P1 | R3 | OPEN |
| CONS-006 | Cross-model consistency | ConsentForm.patient can differ from the patient of its related document. | domain_coherence/G2_COHERENCE_TRACKER.md — G2-CHECK-11, Cross-Patient Consent Inconsistency | P1 | R3 | OPEN |
| RULE-001 | Business rules | Appointment accepts end_at less than or equal to start_at. | BUSINESS_RULE_MATRIX.md — Appointments end/start rule | P1 | R4 | OPEN |
| RULE-002 | Business rules | Appointment scheduling accepts overlapping room, practitioner, or patient reservations. | BUSINESS_RULE_MATRIX.md — Appointments overlap rule | P1 | R4 | OPEN |
| RULE-003 | Business rules | Payment accepts non-positive amounts and amounts exceeding the outstanding invoice balance. | BUSINESS_RULE_MATRIX.md — Billing payment amount rule | P0 | R4 | OPEN |
| RULE-004 | Business rules | Calculated invoice totals and balances are client-writable through the API contract. | BUSINESS_RULE_MATRIX.md — Billing calculated totals/balances rule | P0 | R4 | OPEN |
| RULE-005 | Business rules | Inventory stock quantities can become negative. | BUSINESS_RULE_MATRIX.md — Inventory negative stock rule | P1 | R4 | OPEN |
| STATE-001 | State machine integrity | Appointment status can jump directly between any defined choices without transition enforcement. | STATE_MACHINE_AUDIT.md — Appointment.status | P1 | R5 | OPEN |
| STATE-002 | State machine integrity | Appointment status choices are not enforced through ORM writes and invalid values can be persisted. | STATE_MACHINE_AUDIT.md — Appointment.status ORM bypass | P1 | R5 | OPEN |
| STATE-003 | State machine integrity | Exposed workflow status fields accept arbitrary free-text values through the API. | STATE_MACHINE_AUDIT.md — exposed free-text status fields | P1 | R5 | OPEN |
| AUTH-001 | Authorization | Patient-linked documents are exposed to every active staff role without patient, ownership, practitioner, or confidentiality scoping. | SECURITY_AUDIT.md — SEC-001 | P1 | R7 | OPEN |
| FILE-001 | File integrity and lifecycle | Clinical file upload boundaries accept files without evidenced size, extension, MIME/content, or file-signature validation. | SECURITY_AUDIT.md — SEC-002 | P1 | R8 | OPEN |
| AUTH-002 | Authorization | Login endpoint lacks evidenced throttling, lockout, or equivalent brute-force protection. | SECURITY_AUDIT.md — SEC-003 | P1 | R7 | OPEN |
| AUTH-003 | Authorization | Authentication tokens are persistent and reused across login events without evidenced expiry, rotation, revocation, or per-session lifecycle enforcement. | SECURITY_AUDIT.md — SEC-004 | P1 | R7 | OPEN |
| SEC-001 | Security configuration and operational hardening | Production Django transport and cookie security policy is not evidenced across the inspected settings and runtime configuration. | SECURITY_AUDIT.md — SEC-005 | P1 | R11 | OPEN |
| SEC-002 | Security configuration and operational hardening | Django can start with a known static SECRET_KEY fallback when runtime configuration is absent. | SECURITY_AUDIT.md — SEC-006 | P1 | R11 | OPEN |
| SEC-003 | Security configuration and operational hardening | Backend container does not enforce a non-root runtime identity. | SECURITY_AUDIT.md — SEC-008 | P1 | R11 | OPEN |
| SEC-004 | Security configuration and operational hardening | Python dependencies are not reproducibly locked to exact resolved versions. | SECURITY_AUDIT.md — SEC-009 | P1 | R11 | OPEN |
| SEC-005 | Security configuration and operational hardening | Development database credentials and PostgreSQL host exposure are embedded in Compose configuration. | SECURITY_AUDIT.md — SEC-010 | P1 | R11 | OPEN |
| SEC-006 | Security configuration and operational hardening | Frontend dependency lockfiles are explicitly excluded from version control. | SECURITY_AUDIT.md — SEC-012 | P2 | R11 | OPEN |
| AUTH-004 | Authorization | Transitional DRF authentication surface remains broader than the intended JWT architecture. | SECURITY_AUDIT.md — SEC-011 | P2 | R7 | OPEN |
## Remediation Tracking

### R1 — Deletion and data-retention integrity

Findings assigned to R1:

- DEL-001
- DEL-002
- DEL-003

### R2 — Serializer ownership and write-contract hardening

Findings assigned to R2:

- SER-001
- SER-002
- SER-003
- SER-004
- SER-005
- SER-006
- SER-007

### R3 — Cross-model consistency

Findings assigned to R3:

- CONS-001
- CONS-002
- CONS-003
- CONS-004
- CONS-005
- CONS-006

### R4 — Business rule enforcement

Findings assigned to R4:

- RULE-001
- RULE-002
- RULE-003
- RULE-004
- RULE-005

### R5 — State machine enforcement

Findings assigned to R5:

- STATE-001
- STATE-002
- STATE-003

### R7 — Authorization scope

Findings assigned to R7:

- AUTH-001
- AUTH-002
- AUTH-003
- AUTH-004

### R8 — File integrity and lifecycle

Findings assigned to R8:

- FILE-001

### R11 — Security hardening

Findings assigned to R11:

- SEC-001
- SEC-002
- SEC-003
- SEC-004
- SEC-005
- SEC-006

#### DEL-001 — SoftDeleteModel does not implement soft deletion

**Status:** OPEN
**Priority:** P0
**Domain:** Deletion and retention
**Remediation phase:** R1

##### Verified finding

`SoftDeleteModel` defines `is_deleted` and `deleted_at`, but does not override `delete()` and does not provide a custom manager or queryset that filters deleted records.

Calls to `Model.delete()` therefore still perform hard deletion and can trigger configured `CASCADE` chains.

##### Audit evidence

- `MODEL_RELATIONSHIP_GRAPH.md`
  - `B1.C — Soft delete is not implemented (flag fields only)`
  - `B1.F — Integrity risk summary`

##### Integrity risk

Code may assume that models inheriting `SoftDeleteModel` are protected by soft-delete semantics while destructive hard deletion remains active.

##### Required remediation

Define and enforce safe deletion semantics for models inheriting `SoftDeleteModel`.

The remediation must prevent accidental hard deletion through the normal deletion path without inventing unsupported retention policy.

##### Dependencies

None.

##### Implementation evidence

Not implemented.

##### Validation strategy

- verify normal deletion does not physically remove a soft-deletable record,
- verify deletion metadata is recorded,
- verify deleted-record query behavior,
- verify destructive cascade chains are not triggered by the normal deletion path,
- run `manage.py check`,
- run the full Django test suite,
- run `python3 -m compileall -q .`,
- run `git diff --check`.

##### Validation evidence

Not validated.

##### B14 freeze status

Not ready for backend contract freeze.

#### DEL-002 — Patient hard deletion cascades across business history

**Status:** OPEN
**Priority:** P0
**Domain:** Deletion and retention
**Remediation phase:** R1

##### Verified finding

Hard deletion of a `Patient` cascades across multiple clinical, billing, imaging, and document relationships.

The audited deletion graph confirms that patient deletion can remove appointments, odontogram data, treatment plans, treatments, prescriptions, invoices, documents, and imaging records together with dependent history.

##### Audit evidence

- `MODEL_RELATIONSHIP_GRAPH.md`
  - `B1.D — Patient`
  - `B1.F — Integrity risk summary`

##### Integrity risk

A destructive patient deletion can irreversibly remove clinical and financial history across multiple backend domains.

##### Required remediation

Prevent the normal patient deletion path from triggering destructive cross-domain cascade deletion.

Deletion behavior must remain compatible with the safe deletion semantics established by DEL-001.

##### Dependencies

- DEL-001

##### Implementation evidence

Not implemented.

##### Validation strategy

- verify normal patient deletion does not physically remove the patient row,
- verify clinical history remains persisted,
- verify billing history remains persisted,
- verify document and imaging records remain persisted,
- verify deletion metadata is recorded,
- run `manage.py check`,
- run the full Django test suite,
- run `python3 -m compileall -q .`,
- run `git diff --check`.

##### Validation evidence

Not validated.

##### B14 freeze status

Not ready for backend contract freeze.

#### DEL-003 — Invoice deletion can remove financial history

**Status:** OPEN
**Priority:** P0
**Domain:** Deletion and retention
**Remediation phase:** R1

##### Verified finding

Hard deletion of an `Invoice` cascades to related `InvoiceLine`, `Payment`, and `CreditNote` records.

The audited deletion graph explicitly identifies invoice deletion as a financial ledger and history risk.

##### Audit evidence

- `MODEL_RELATIONSHIP_GRAPH.md`
  - `B1.D — Invoice / Payment`
  - `B1.F — Integrity risk summary`

##### Integrity risk

Deleting an invoice can remove payment and credit-note history required to preserve financial record integrity.

##### Required remediation

Prevent the normal invoice deletion path from destructively removing invoice financial history.

The remediation must define safe invoice deletion behavior without introducing unsupported financial retention policy.

##### Dependencies

- DEL-001

##### Implementation evidence

Not implemented.

##### Validation strategy

- verify normal invoice deletion does not physically remove protected financial history,
- verify related payments remain persisted,
- verify related credit notes remain persisted,
- verify invoice deletion behavior is explicit and regression-tested,
- run `manage.py check`,
- run the full Django test suite,
- run `python3 -m compileall -q .`,
- run `git diff --check`.

##### Validation evidence

Not validated.

##### B14 freeze status

Not ready for backend contract freeze.

#### SER-001 — Broad writable contracts through fields='__all__'

**Status:** OPEN
**Priority:** P1
**Domain:** Serializer and API write contract
**Remediation phase:** R2

##### Verified finding

Most exposed serializers are `ModelSerializer` implementations using `fields = '__all__'`.

This broad contract exposes model fields as writable unless explicitly restricted and includes fields that are backend-controlled or business-sensitive.

##### Audit evidence

- `SERIALIZER_CONTRACT_AUDIT.md`
  - `Executive summary — Key integrity risks`
  - `Unsafe writable field findings`

##### Integrity risk

API clients can submit values for fields whose ownership should belong to backend workflow logic rather than the request payload.

This creates a broad mass-assignment surface and allows business-sensitive fields to be modified without an explicit serializer contract.

##### Required remediation

Replace broad implicit write contracts with explicit serializer field ownership.

Backend-controlled fields must be made read-only or assigned through server-side workflow logic according to the verified domain rules.

##### Dependencies

- DEL-001

##### Implementation evidence

Not implemented.

##### Validation strategy

- audit all exposed serializers currently using `fields = '__all__'`,
- verify backend-controlled fields are not client-writable,
- verify intended business input fields remain writable,
- add API contract regression tests,
- add negative tests for server-owned field submission,
- run `manage.py check`,
- run the full Django test suite,
- run `python3 -m compileall -q .`,
- run `git diff --check`.

##### Validation evidence

Not validated.

##### B14 freeze status

Not ready for backend contract freeze.

#### SER-002 — Soft-delete metadata is client-writable

**Status:** OPEN
**Priority:** P1
**Domain:** Serializer and API write contract
**Remediation phase:** R2

##### Verified finding

Serializers for `Patient`, `Appointment`, `Odontogram`, `Tooth`, `TreatmentPlan`, and `Treatment` expose all model fields through `fields = '__all__'`.

Because these models inherit `SoftDeleteModel`, the `is_deleted` and `deleted_at` fields are exposed as writable API fields.

##### Audit evidence

- `SERIALIZER_CONTRACT_AUDIT.md`
  - `Executive summary — Key integrity risks`
  - `Model/serializer mismatch findings — Soft-delete fields exposed as writable`

##### Integrity risk

API clients can directly modify deletion state and deletion metadata without using backend-controlled deletion semantics.

A client can set `is_deleted=True` and cause resources to disappear from ViewSets filtering on `is_deleted=False`.

##### Required remediation

Make `is_deleted` and `deleted_at` server-controlled fields in exposed serializer contracts.

Deletion metadata must only be changed through the safe deletion behavior established by R1.

##### Dependencies

- DEL-001
- SER-001

##### Implementation evidence

Not implemented.

##### Validation strategy

- verify `is_deleted` is not client-writable,
- verify `deleted_at` is not client-writable,
- verify create and update payloads cannot control deletion metadata,
- verify backend deletion semantics can still update deletion metadata,
- add API contract and negative payload tests,
- run `manage.py check`,
- run the full Django test suite,
- run `python3 -m compileall -q .`,
- run `git diff --check`.

##### Validation evidence

Not validated.

##### B14 freeze status

Not ready for backend contract freeze.

#### SER-003 — Attribution and workflow metadata is client-writable

**Status:** OPEN
**Priority:** P1
**Domain:** Serializer and API write contract
**Remediation phase:** R2

##### Verified finding

Exposed serializers allow clients to write attribution and workflow audit-like fields without explicit server-side ownership enforcement.

Verified writable fields include:

- `Appointment.created_by`
- `Appointment.confirmed_by`
- `Appointment.cancelled_by`
- `Appointment.confirmed_at`
- `Appointment.cancelled_at`
- `TreatmentPlan.created_by`
- `Document.created_by`
- `Payment.paid_by`

##### Audit evidence

- `SERIALIZER_CONTRACT_AUDIT.md`
  - `Executive summary — Key integrity risks`
  - `Unsafe writable field findings — Attribution / audit-like fields`

##### Integrity risk

API clients can directly assign actor attribution and workflow timestamps that may be interpreted as backend-generated business history.

This weakens provenance and allows request payloads to control audit-sensitive metadata.

##### Required remediation

Make verified attribution and workflow metadata server-controlled at the API write boundary.

Values must be assigned by authenticated backend workflow logic where ownership semantics are defined.

##### Dependencies

- SER-001

##### Implementation evidence

Not implemented.

##### Validation strategy

- verify audited attribution fields are not client-writable,
- verify audited workflow timestamps are not client-writable,
- add negative create and update payload tests,
- verify server-side workflows can assign supported attribution metadata,
- run `manage.py check`,
- run the full Django test suite,
- run `python3 -m compileall -q .`,
- run `git diff --check`.

##### Validation evidence

Not validated.

##### B14 freeze status

Not ready for backend contract freeze.

#### SER-004 — User password requiredness contract is inconsistent

**Status:** OPEN
**Priority:** P2
**Domain:** Serializer and API write contract
**Remediation phase:** R2

##### Verified finding

The user serializer declares `password` with `required=False`.

Its `create()` implementation raises an error when the password is missing.

The serializer schema therefore presents the password as optional while the creation path requires it.

##### Audit evidence

- `SERIALIZER_CONTRACT_AUDIT.md`
  - `Model/serializer mismatch findings — User password requiredness`

##### Integrity risk

API clients can derive an incorrect request contract from serializer metadata and submit a payload that passes declared requiredness expectations but fails during creation.

##### Required remediation

Align the serializer-declared password requiredness with the actual user creation behavior.

The API contract and implementation must express the same requirement.

##### Dependencies

- SER-001

##### Implementation evidence

Not implemented.

##### Validation strategy

- verify serializer metadata reflects actual password requiredness,
- verify user creation without a required password fails at serializer validation,
- verify valid user creation remains supported,
- add serializer contract regression tests,
- run `manage.py check`,
- run the full Django test suite,
- run `python3 -m compileall -q .`,
- run `git diff --check`.

##### Validation evidence

Not validated.

##### B14 freeze status

Not ready for backend contract freeze.

#### SER-005 — AuditLogSerializer exposes a writable serializer contract

**Status:** OPEN
**Priority:** P2
**Domain:** Serializer and API write contract
**Remediation phase:** R2

##### Verified finding

`AuditLogSerializer` exposes model fields through a writable serializer contract.

The currently exposed API ViewSet is read-only, but the serializer itself does not enforce read-only semantics for audit log data.

##### Audit evidence

- `SERIALIZER_CONTRACT_AUDIT.md`
  - `Executive summary — WARN findings`

##### Integrity risk

If `AuditLogSerializer` is reused in a writable API path, request payloads could control audit log fields that represent backend-generated audit history.

The current read-only ViewSet limits immediate exposure but does not make the serializer contract itself safe for reuse.

##### Required remediation

Make the audit log serializer contract explicitly read-only for backend-generated audit data.

The serializer must not depend solely on the current ViewSet type to prevent client-controlled audit history.

##### Dependencies

- SER-001

##### Implementation evidence

Not implemented.

##### Validation strategy

- verify audit log fields are not client-writable,
- verify serializer create and update paths cannot accept client-controlled audit history,
- verify existing read-only API behavior remains unchanged,
- add serializer contract regression tests,
- run `manage.py check`,
- run the full Django test suite,
- run `python3 -m compileall -q .`,
- run `git diff --check`.

##### Validation evidence

Not validated.

##### B14 freeze status

Not ready for backend contract freeze.

#### SER-006 — Login request contract is not serializer-defined

**Status:** OPEN
**Priority:** P2
**Domain:** Serializer and API write contract
**Remediation phase:** R2

##### Verified finding

`LoginView` parses request data manually without using a serializer-defined request contract.

The login request structure is therefore validated through view logic rather than an explicit serializer contract.

##### Audit evidence

- `SERIALIZER_CONTRACT_AUDIT.md`
  - `Executive summary — WARN findings`
  - `Authentication request/response contract`

##### Integrity risk

The login API request contract is loosely defined and cannot rely on serializer metadata or serializer validation behavior.

This increases the risk of inconsistent validation, unclear requiredness, and contract drift between API behavior and client expectations.

##### Required remediation

Define an explicit serializer-based request contract for login input.

The serializer must validate the supported login fields and requiredness without changing verified authentication behavior.

##### Dependencies

- SER-001

##### Implementation evidence

Not implemented.

##### Validation strategy

- verify login input is validated through an explicit serializer,
- verify required login fields are contractually defined,
- verify malformed login payloads fail at serializer validation,
- verify valid authentication behavior remains unchanged,
- verify failed authentication behavior remains unchanged,
- add login request contract regression tests,
- run `manage.py check`,
- run the full Django test suite,
- run `python3 -m compileall -q .`,
- run `git diff --check`.

##### Validation evidence

Not validated.

##### B14 freeze status

Not ready for backend contract freeze.

#### CONS-001 — Invoice patient can differ from related treatment-plan patient

**Status:** OPEN
**Priority:** P1
**Domain:** Cross-model consistency
**Remediation phase:** R3

##### Verified finding

The backend accepts an `Invoice` whose `patient` differs from the patient associated with its `related_treatment_plan`.

The API accepts this inconsistent relationship with HTTP 201.

##### Audit evidence

- `CROSS_MODEL_CONSISTENCY_AUDIT.md`
  - `B3-002`

##### Integrity risk

An invoice can be assigned to one patient while referencing a treatment plan belonging to another patient.

This creates inconsistent billing and clinical ownership across patient-scoped records.

##### Required remediation

Enforce patient consistency between an invoice and its related treatment plan.

When `related_treatment_plan` is present, `Invoice.patient` must match `related_treatment_plan.patient`.

##### Dependencies

- SER-001

##### Implementation evidence

Not implemented.

##### Validation strategy

- verify mismatched invoice and treatment-plan patients are rejected,
- verify matching patient relationships remain accepted,
- verify invoices without a related treatment plan remain supported,
- add API and model consistency regression tests,
- run `manage.py check`,
- run the full Django test suite,
- run `python3 -m compileall -q .`,
- run `git diff --check`.

##### Validation evidence

Not validated.

##### B14 freeze status

Not ready for backend contract freeze.

#### CONS-002 — Treatment patient can differ from appointment patient

**Status:** OPEN
**Priority:** P1
**Domain:** Cross-model consistency
**Remediation phase:** R3

##### Verified finding

The backend accepts a `Treatment` whose `patient` differs from the patient associated with its referenced `appointment`.

The API accepts this inconsistent relationship with HTTP 201.

##### Audit evidence

- `CROSS_MODEL_CONSISTENCY_AUDIT.md`
  - `B3-003`

##### Integrity risk

A treatment can be assigned to one patient while referencing an appointment belonging to another patient.

This creates inconsistent clinical ownership across patient-scoped records.

##### Required remediation

Enforce patient consistency between a treatment and its referenced appointment.

When `appointment` is present, `Treatment.patient` must match `appointment.patient`.

##### Dependencies

- SER-001

##### Implementation evidence

Not implemented.

##### Validation strategy

- verify mismatched treatment and appointment patients are rejected,
- verify matching patient relationships remain accepted,
- verify treatments without an appointment remain supported,
- add API and model consistency regression tests,
- run `manage.py check`,
- run the full Django test suite,
- run `python3 -m compileall -q .`,
- run `git diff --check`.

##### Validation evidence

Not validated.

##### B14 freeze status

Not ready for backend contract freeze.

#### CONS-003 — Treatment patient can differ from treatment-plan patient

**Status:** OPEN
**Priority:** P1
**Domain:** Cross-model consistency
**Remediation phase:** R3

##### Verified finding

The backend accepts a `Treatment` whose `patient` differs from the patient associated with its referenced `treatment_plan`.

The API accepts this inconsistent relationship with HTTP 201.

##### Audit evidence

- `CROSS_MODEL_CONSISTENCY_AUDIT.md`
  - `B3-004`

##### Integrity risk

A treatment can be assigned to one patient while referencing a treatment plan belonging to another patient.

This creates inconsistent clinical ownership across patient-scoped records.

##### Required remediation

Enforce patient consistency between a treatment and its referenced treatment plan.

When `treatment_plan` is present, `Treatment.patient` must match `treatment_plan.patient`.

##### Dependencies

- SER-001

##### Implementation evidence

Not implemented.

##### Validation strategy

- verify mismatched treatment and treatment-plan patients are rejected,
- verify matching patient relationships remain accepted,
- verify treatments without a treatment plan remain supported,
- add API and model consistency regression tests,
- run `manage.py check`,
- run the full Django test suite,
- run `python3 -m compileall -q .`,
- run `git diff --check`.

##### Validation evidence

Not validated.

##### B14 freeze status

Not ready for backend contract freeze.

#### CONS-004 — Treatment-plan approval patient can differ from plan patient

**Status:** OPEN
**Priority:** P1
**Domain:** Cross-model consistency
**Remediation phase:** R3

##### Verified finding

The backend accepts a `TreatmentPlanApproval` whose `patient` differs from the patient associated with its `treatment_plan`.

The inconsistent relationship is accepted through the ORM.

`TreatmentPlanApproval` is not exposed as an API resource in the audited API surface.

##### Audit evidence

- `CROSS_MODEL_CONSISTENCY_AUDIT.md`
  - `B3-005`

##### Integrity risk

A treatment-plan approval can be assigned to one patient while referencing a treatment plan belonging to another patient.

This creates inconsistent clinical approval ownership across patient-scoped records.

##### Required remediation

Enforce patient consistency between a treatment-plan approval and its treatment plan.

`TreatmentPlanApproval.patient` must match `treatment_plan.patient`.

##### Dependencies

None.

##### Implementation evidence

Not implemented.

##### Validation strategy

- verify ORM creation with mismatched approval and treatment-plan patients is rejected,
- verify matching patient relationships remain accepted,
- add model consistency regression tests,
- verify no unintended API exposure is introduced,
- run `manage.py check`,
- run the full Django test suite,
- run `python3 -m compileall -q .`,
- run `git diff --check`.

##### Validation evidence

Not validated.

##### B14 freeze status

Not ready for backend contract freeze.

#### CONS-005 — Document attachment patient can differ from document patient

**Status:** OPEN
**Priority:** P1
**Domain:** Cross-model consistency
**Remediation phase:** R3

##### Verified finding

`DocumentAttachment` contains both a direct `patient` relation and an optional `document` relation.

When `document` is present, the backend does not enforce that `DocumentAttachment.patient` matches `DocumentAttachment.document.patient`.

The current model therefore permits a document attachment assigned to one patient while referencing a document belonging to another patient.

##### Audit evidence

* `domain_coherence/G2_COHERENCE_TRACKER.md`

  * `G2-CHECK-11 — Document Management`
  * `Cross-Patient Attachment Inconsistency`
  * `Proposal G2-P57`

##### Integrity risk

A document attachment can expose conflicting patient ownership through two independent relation paths.

When a document is present, the document already determines patient ownership, while `DocumentAttachment.patient` remains a second unconstrained source of patient ownership truth.

This can associate a clinical or confidential file with a patient different from the patient owning the related document.

##### Required remediation

Enforce patient consistency between a document attachment and its related document.

When `document` is not null, `DocumentAttachment.patient` must match `document.patient`.

The R3 remediation must enforce the existing invariant without prematurely consolidating `documents.DocumentAttachment` and `patients.PatientAttachment`.

The final ownership and model consolidation decision remains dependent on the G11 document-management domain review.

##### Dependencies

* CONS-006
* DEL-002
* AUTH-001
* FILE-001
* G11 document-management domain validation

##### Implementation evidence

Not implemented.

##### Validation strategy

* verify ORM creation with mismatched attachment and document patients is rejected,
* verify matching patient relationships remain accepted,
* verify document attachments without a document remain supported,
* verify updates cannot introduce a cross-patient attachment/document mismatch,
* add model consistency regression tests,
* verify no unintended direct API exposure of `DocumentAttachment` is introduced,
* run `manage.py check`,
* run the full Django test suite,
* run `python3 -m compileall -q .`,
* run `git diff --check`.

##### Validation evidence

Not validated.

##### B14 freeze status

Not ready for backend contract freeze.

#### CONS-006 — Consent form patient can differ from document patient

**Status:** OPEN
**Priority:** P1
**Domain:** Cross-model consistency
**Remediation phase:** R3

##### Verified finding

`ConsentForm` contains both a direct `patient` relation and a `document` relation.

When a document is associated, the backend does not enforce that `ConsentForm.patient` matches `ConsentForm.document.patient`.

The current model therefore permits a consent record assigned to one patient while referencing a document belonging to another patient.

##### Audit evidence

* `domain_coherence/G2_COHERENCE_TRACKER.md`

  * `G2-CHECK-11 — Document Management`
  * `Cross-Patient Consent Inconsistency`

##### Integrity risk

A consent record can expose conflicting patient ownership through two independent relation paths.

When a document is present, the document already determines patient ownership, while `ConsentForm.patient` remains a second unconstrained source of patient ownership truth.

This can associate a clinical consent with a patient different from the patient owning the related document.

##### Required remediation

Enforce patient consistency between a consent form and its related document.

`ConsentForm.patient` must always match `ConsentForm.document.patient`.

The R3 remediation must enforce the existing invariant without prematurely consolidating `documents.ConsentForm` and `patients.PatientConsent`.

The final ownership and model consolidation decision remains dependent on the G11 document-management domain review.

##### Dependencies

* DEL-002
* AUTH-001
* FILE-001
* G11 document-management domain validation

##### Implementation evidence

Not implemented.

##### Validation strategy

* verify ORM creation with mismatched consent and document patients is rejected,
* verify matching patient relationships remain accepted,
* verify updates cannot introduce a cross-patient consent/document mismatch,
* add model consistency regression tests,
* verify no unintended direct API exposure of `ConsentForm` is introduced,
* run `manage.py check`,
* run the full Django test suite,
* run `python3 -m compileall -q .`,
* run `git diff --check`.

##### Validation evidence

Not validated.

##### B14 freeze status

Not ready for backend contract freeze.

#### RULE-001 — Appointment accepts invalid chronological intervals

**Status:** OPEN
**Priority:** P1
**Domain:** Business rules
**Remediation phase:** R4

##### Verified finding

The backend accepts an `Appointment` whose `end_at` is less than or equal to `start_at`.

The invalid chronological interval is accepted by the current backend.

##### Audit evidence

- `BUSINESS_RULE_MATRIX.md`
  - Appointments — `end_at > start_at`

##### Integrity risk

An appointment can end before it starts or have a zero-duration interval.

This creates invalid scheduling records and undermines duration, availability, and overlap calculations.

##### Required remediation

Enforce chronological consistency for appointment intervals.

`Appointment.end_at` must be strictly greater than `Appointment.start_at`.

##### Dependencies

None.

##### Implementation evidence

Not implemented.

##### Validation strategy

- verify appointments with `end_at < start_at` are rejected,
- verify appointments with `end_at == start_at` are rejected,
- verify appointments with `end_at > start_at` remain accepted,
- add API and model business-rule regression tests,
- run `manage.py check`,
- run the full Django test suite,
- run `python3 -m compileall -q .`,
- run `git diff --check`.

##### Validation evidence

Not validated.

##### B14 freeze status

Not ready for backend contract freeze.

#### RULE-002 — Appointment scheduling accepts overlapping reservations

**Status:** OPEN
**Priority:** P1
**Domain:** Business rules
**Remediation phase:** R4

##### Verified finding

The backend accepts overlapping appointment intervals for the same room, practitioner, or patient.

The current scheduling contract does not enforce reservation overlap constraints.

##### Audit evidence

- `BUSINESS_RULE_MATRIX.md`
  - Appointments — overlap constraints for room, practitioner, and patient scheduling

##### Integrity risk

Multiple appointments can reserve the same room, practitioner, or patient during overlapping time intervals.

This creates conflicting schedules and allows operationally impossible appointment reservations.

##### Required remediation

Enforce appointment overlap constraints for shared scheduling resources.

An appointment interval must not overlap another active appointment interval for the same room, practitioner, or patient.

##### Dependencies

- RULE-001

##### Implementation evidence

Not implemented.

##### Validation strategy

- verify overlapping appointments for the same room are rejected,
- verify overlapping appointments for the same practitioner are rejected,
- verify overlapping appointments for the same patient are rejected,
- verify non-overlapping appointments remain accepted,
- verify adjacent intervals remain supported,
- add API and model scheduling regression tests,
- run `manage.py check`,
- run the full Django test suite,
- run `python3 -m compileall -q .`,
- run `git diff --check`.

##### Validation evidence

Not validated.

##### B14 freeze status

Not ready for backend contract freeze.

#### RULE-003 — Payment accepts invalid amounts and invoice overpayment

**Status:** OPEN
**Priority:** P0
**Domain:** Business rules
**Remediation phase:** R4

##### Verified finding

The backend accepts a `Payment` with a non-positive amount.

The backend also accepts a payment amount exceeding the outstanding balance of its related invoice.

These invalid billing states are accepted by the current backend.

##### Audit evidence

- `BUSINESS_RULE_MATRIX.md`
  - Billing — payment amount must be positive and less than or equal to outstanding balance

##### Integrity risk

A zero or negative payment can corrupt payment history and financial calculations.

An excessive payment can overpay an invoice and produce an invalid negative outstanding balance.

This undermines billing integrity and financial reporting.

##### Required remediation

Enforce payment amount and invoice balance integrity.

`Payment.amount` must be strictly greater than zero.

A payment amount must not exceed the current outstanding balance of its related invoice.

Payment validation and invoice balance updates must be performed atomically.

##### Dependencies

- SER-001
- RULE-004

##### Implementation evidence

Not implemented.

##### Validation strategy

- verify zero-value payments are rejected,
- verify negative payments are rejected,
- verify payments exceeding the outstanding invoice balance are rejected,
- verify payments equal to the outstanding balance remain accepted,
- verify partial payments remain accepted,
- verify concurrent payment operations cannot overpay an invoice,
- add API and model billing regression tests,
- run `manage.py check`,
- run the full Django test suite,
- run `python3 -m compileall -q .`,
- run `git diff --check`.

##### Validation evidence

Not validated.

##### B14 freeze status

Not ready for backend contract freeze.

#### RULE-004 — Calculated invoice totals and balances are client-writable

**Status:** OPEN
**Priority:** P0
**Domain:** Business rules
**Remediation phase:** R4

##### Verified finding

The current invoice API contract exposes calculated totals and balance fields as writable client-controlled data.

The serializer contract does not enforce server ownership of these financial values.

##### Audit evidence

- `BUSINESS_RULE_MATRIX.md`
  - Billing — calculated invoice totals and balances should not be client-writable
- `SERIALIZER_CONTRACT_AUDIT.md`
  - Unsafe writable field findings

##### Integrity risk

A client can submit or modify calculated financial values independently of invoice line items and payment history.

This can create inconsistent totals, incorrect outstanding balances, and unreliable financial reporting.

##### Required remediation

Make calculated invoice totals and balances server-controlled.

Calculated financial fields must be read-only through the API contract.

Invoice totals and outstanding balances must be derived from authoritative billing data on the server.

##### Dependencies

- SER-001

##### Implementation evidence

Not implemented.

##### Validation strategy

- verify clients cannot set calculated invoice totals during creation,
- verify clients cannot modify calculated invoice totals during update,
- verify clients cannot set or modify outstanding balance values,
- verify invoice totals are derived from authoritative billing data,
- verify outstanding balances reflect accepted payments,
- add API billing contract regression tests,
- run `manage.py check`,
- run the full Django test suite,
- run `python3 -m compileall -q .`,
- run `git diff --check`.

##### Validation evidence

Not validated.

##### B14 freeze status

Not ready for backend contract freeze.

#### RULE-005 — Inventory stock quantities can become negative

**Status:** OPEN
**Priority:** P1
**Domain:** Business rules
**Remediation phase:** R4

##### Verified finding

The backend accepts inventory state changes that allow stock quantities to become negative.

The current inventory contract does not enforce a non-negative stock invariant.

##### Audit evidence

- `BUSINESS_RULE_MATRIX.md`
  - Inventory — stock quantities must not go negative

##### Integrity risk

Inventory records can represent unavailable negative quantities.

This creates unreliable stock availability, invalid inventory reporting, and can allow operations to consume stock that does not exist.

##### Required remediation

Enforce non-negative inventory stock quantities.

Inventory quantities must remain greater than or equal to zero after every stock-changing operation.

Stock validation and quantity updates must be performed atomically.

##### Dependencies

None.

##### Implementation evidence

Not implemented.

##### Validation strategy

- verify direct negative stock quantities are rejected,
- verify stock-changing operations cannot reduce quantity below zero,
- verify valid stock reductions remain accepted,
- verify stock can reach exactly zero,
- verify concurrent stock operations cannot produce negative quantities,
- add API and model inventory regression tests,
- run `manage.py check`,
- run the full Django test suite,
- run `python3 -m compileall -q .`,
- run `git diff --check`.

##### Validation evidence

Not validated.

##### B14 freeze status

Not ready for backend contract freeze.

#### STATE-001 — Appointment status transitions are not enforced

**Status:** OPEN
**Priority:** P1
**Domain:** State machine integrity
**Remediation phase:** R5

##### Verified finding

`Appointment.status` defines explicit Django choices for `pending`, `confirmed`, `completed`, `cancelled`, and `no_show`.

The backend does not define or enforce an explicit transition policy between these states.

Any valid status choice can therefore be changed directly to any other valid status choice without transition validation.

##### Audit evidence

- `STATE_MACHINE_AUDIT.md`
  - `Executive summary`
  - `Appointment.status`
  - `Any choice can be set from any other choice`

##### Integrity risk

Appointment workflow state can bypass the intended business sequence.

Terminal or workflow-sensitive states can be changed directly without explicit transition authorization or transition validation.

This prevents the appointment lifecycle from being treated as an enforceable backend state machine.

##### Required remediation

Define and enforce an explicit transition policy for `Appointment.status`.

Status changes must pass through backend-controlled transition logic that validates the current state and requested target state.

The remediation must not invent unsupported workflow transitions without first deriving the intended lifecycle from verified backend behavior and project documentation.

##### Dependencies

None.

##### Implementation evidence

Not implemented.

##### Validation strategy

- verify explicitly allowed appointment status transitions are accepted,
- verify forbidden appointment status transitions are rejected,
- verify status cannot jump arbitrarily between defined choices,
- verify transition validation applies to API writes,
- verify transition validation applies to backend workflow paths,
- add state-transition regression tests,
- run `manage.py check`,
- run the full Django test suite,
- run `python3 -m compileall -q .`,
- run `git diff --check`.

##### Validation evidence

Not validated.

##### B14 freeze status

Not ready for backend contract freeze.

#### STATE-002 — Appointment status choices are not enforced through ORM writes

**Status:** OPEN
**Priority:** P1
**Domain:** State machine integrity
**Remediation phase:** R5

##### Verified finding

`Appointment.status` defines Django model choices for `pending`, `confirmed`, `completed`, `cancelled`, and `no_show`.

The API serializer constrains the field through DRF `ChoiceField` behavior and rejects invalid status values.

Direct ORM writes are not constrained by Django model choices.

The ORM can therefore persist an arbitrary string in `Appointment.status`, and the database does not enforce the defined choices.

##### Audit evidence

- `STATE_MACHINE_AUDIT.md`
  - `Executive summary`
  - `Appointment.status`
  - `ORM can save invalid values because Django choices are not DB-enforced`
  - `test_orm_appointment_status_choices_not_enforced`

##### Integrity risk

Appointment records can contain status values outside the defined workflow vocabulary when written through ORM paths.

Backend code that assumes every persisted appointment status belongs to the declared choices can therefore operate on invalid workflow state.

API-level choice validation alone does not protect model or database integrity.

##### Required remediation

Enforce valid `Appointment.status` values beyond the API serializer boundary.

ORM-backed appointment writes must not persist status values outside the verified appointment status vocabulary.

The remediation must remain compatible with the explicit transition enforcement required by STATE-001.

##### Dependencies

- STATE-001

##### Implementation evidence

Not implemented.

##### Validation strategy

- verify direct ORM writes cannot persist an undefined appointment status,
- verify all defined appointment status choices remain supported,
- verify API rejection of invalid status values remains enforced,
- verify status-value validation remains compatible with appointment transition enforcement,
- add model and ORM status-integrity regression tests,
- run `manage.py check`,
- run the full Django test suite,
- run `python3 -m compileall -q .`,
- run `git diff --check`.

##### Validation evidence

Not validated.

##### B14 freeze status

Not ready for backend contract freeze.

#### STATE-003 — Exposed workflow status fields accept arbitrary free-text values

**Status:** OPEN
**Priority:** P1
**Domain:** State machine integrity
**Remediation phase:** R5

##### Verified finding

Multiple workflow-oriented `status` fields are exposed through API serializers without explicit model choices or another verified constrained state vocabulary.

The audited API paths accept arbitrary string values for exposed workflow status fields.

Verified affected API-exposed models include:

- `treatments.Treatment`,
- `treatment_plans.TreatmentPlan`,
- `prescriptions.Prescription`,
- `billing.Invoice`,
- `billing.Payment`,
- `documents.Document`,
- `notifications.Notification`,
- `imaging.ImagingStudy`,
- `staff.StaffProfile`,
- `odontogram.Tooth`.

`Patient.marital_status` and `Tooth.surface_status` are excluded because the state-machine audit identifies them as data attributes rather than workflow states.

##### Audit evidence

- `STATE_MACHINE_AUDIT.md`
  - `Executive summary`
  - `State machine matrix`
  - exposed API paths accepting arbitrary status strings
  - existing B5 status behavior tests where recorded

##### Integrity risk

Workflow state can be populated with arbitrary vocabulary through exposed API write paths.

Backend logic cannot reliably reason about lifecycle state when persisted values are unconstrained and no explicit state vocabulary is defined.

Different clients or backend paths can introduce incompatible status values for the same workflow domain.

##### Required remediation

Define explicit, verified state vocabularies for API-exposed workflow status fields.

API writes must reject status values outside the state vocabulary defined for the affected workflow model.

Where a field represents a true lifecycle state, status mutation must remain compatible with any explicit transition policy defined for that model.

The remediation must not invent workflow states or transitions without first deriving them from verified backend behavior and project documentation.

##### Dependencies

None.

##### Implementation evidence

Not implemented.

##### Validation strategy

- verify each affected API-exposed workflow status field rejects arbitrary undefined values,
- verify explicitly defined status values remain accepted,
- verify data attributes identified as non-workflow fields are not incorrectly converted into state machines,
- verify serializer validation and backend model contracts remain aligned,
- add API status-vocabulary regression tests for affected exposed models,
- run `manage.py check`,
- run the full Django test suite,
- run `python3 -m compileall -q .`,
- run `git diff --check`.

##### Validation evidence

Not validated.

##### B14 freeze status

Not ready for backend contract freeze.
#### AUTH-001 — Patient-linked documents are exposed to every active staff role

**Status:** OPEN
**Priority:** P1
**Domain:** Authorization
**Remediation phase:** R7

##### Verified finding

`DocumentViewSet` exposes the complete `Document` queryset through `Document.objects.all()`.

Access is controlled by `IsStaffMember`.

`IsStaffMember` accepts every active, non-deleted role defined by `User.Role`, including non-clinical roles such as receptionist and accountant.

`Document.patient` directly links documents to patient records.

No patient, ownership, practitioner, creator, or object-level authorization scope is enforced for the exposed document API.

##### Audit evidence

- `SECURITY_AUDIT.md`
  - `SEC-001 — Patient-linked documents are exposed to every staff role`
  - `DocumentViewSet`
  - `Document.objects.all()`
  - `permission_classes = [IsStaffMember]`
- `AUTHORIZATION_MATRIX.md`
  - `IsStaffMember` allows all active roles
  - `DocumentViewSet` is accessible to all active authenticated roles
  - object-level authorization is not implemented for most resources

##### Integrity risk

Every active staff role accepted by `IsStaffMember` can access the complete patient-linked document queryset through the API.

Non-clinical staff roles can therefore reach patient documents without a verified patient, practitioner, ownership, or confidentiality authorization boundary.

The backend cannot currently enforce a documented least-privilege access policy for patient-linked documents.

##### Required remediation

Define and document the document-access authorization matrix before changing the authorization implementation.

The matrix must explicitly define access by role, API action, patient scope, document type, ownership or creator relationship where applicable, and confidentiality state where applicable.

Replace unrestricted document queryset exposure with an explicitly scoped authorization policy.

Direct object access by known primary key must remain constrained by the same authorization scope.

The remediation must not invent document-access rules without first deriving the intended policy from verified backend behavior and project documentation.

##### Dependencies

None.

##### Implementation evidence

Not implemented.

##### Validation strategy

- verify unauthorized staff roles cannot list patient documents outside their permitted scope,
- verify unauthorized staff roles cannot retrieve patient documents by known primary key,
- verify document create, update, patch, and delete actions follow the documented authorization matrix,
- verify queryset scoping and direct object access enforce the same authorization boundary,
- verify permitted document access remains available to explicitly authorized roles,
- add document authorization and direct-ID regression tests,
- run `manage.py check`,
- run the full Django test suite,
- run `python3 -m compileall -q .`,
- run `git diff --check`.

##### Validation evidence

Not validated.

##### B14 freeze status

Not ready for backend contract freeze.
#### AUTH-002 — Login endpoint lacks evidenced brute-force protection

**Status:** OPEN
**Priority:** P1
**Domain:** Authorization
**Remediation phase:** R7

##### Verified finding

`LoginView` exposes `/api/auth/login/` with `authentication_classes = []` and `permission_classes = [AllowAny]`.

The login view does not define a dedicated DRF throttle class.

The authentication service records login attempts through `log_login_attempt()` and persists source IP, user agent, and success or failure state in `UserLoginHistory`.

The inspected authentication flow does not use this history to enforce an attempt threshold, temporary lockout, progressive delay, account-based rate limiting, or IP-based rate limiting.

The project settings do not define `DEFAULT_THROTTLE_CLASSES` or `DEFAULT_THROTTLE_RATES`.

No alternative middleware or authentication backend was evidenced as enforcing brute-force protection at the login boundary.

##### Audit evidence

- `SECURITY_AUDIT.md`
  - `SEC-003 — Login endpoint lacks evidenced brute-force protection`
  - `LoginView`
  - `UserLoginHistory`
  - absence of dedicated login throttling or equivalent preventive control
- `AUTHORIZATION_MATRIX.md`
  - `/api/auth/login/` is exposed as an anonymous `POST` authentication endpoint

##### Integrity risk

Failed authentication attempts are recorded but repeated authentication attempts are not actively limited by an evidenced application-level preventive control.

A client reaching the login endpoint can repeatedly submit credentials without a verified attempt threshold, cooldown period, temporary lockout, or dedicated rate limit.

`UserLoginHistory` provides audit evidence but does not itself prevent brute-force or credential-stuffing attempts.

##### Required remediation

Define and document a dedicated authentication abuse-protection policy before modifying the login flow.

The policy must explicitly define rate-limit scope, IP-based controls, account or normalized-email-based controls, failed-attempt threshold, observation window, cooldown or temporary lockout duration, successful-login reset behavior, trusted proxy and client-IP handling, audit requirements, and user-enumeration constraints.

Apply a dedicated login throttle or equivalent preventive control according to the verified policy.

Account-aware protection must complement IP-only protection where required.

Generic authentication failure behavior and failed-attempt audit evidence must be preserved.

The remediation must not trust attacker-controlled forwarding headers as authoritative client-IP evidence without explicit trusted-proxy configuration.

##### Dependencies

None.

##### Implementation evidence

Not implemented.

##### Validation strategy

- verify normal login attempts remain available,
- verify repeated failed attempts trigger the defined protection threshold,
- verify account-aware and IP-aware controls follow the documented policy,
- verify successful-login reset behavior follows the documented policy,
- verify cooldown or temporary lockout expiration follows the documented policy,
- verify failed attempts remain recorded in login history,
- verify throttled and invalid authentication responses do not introduce a user-enumeration distinction,
- verify client-IP extraction follows the trusted-proxy policy,
- add brute-force protection regression tests,
- run `manage.py check`,
- run the full Django test suite,
- run `python3 -m compileall -q .`,
- run `git diff --check`.

##### Validation evidence

Not validated.

##### B14 freeze status

Not ready for backend contract freeze.
#### AUTH-003 — Authentication tokens are persistent and reused across login events

**Status:** OPEN
**Priority:** P1
**Domain:** Authorization
**Remediation phase:** R7

##### Verified finding

`issue_token_for_user()` uses `Token.objects.get_or_create(user=user)` and returns the resulting token key.

An existing authentication token is therefore reused when the same user authenticates successfully again.

`login_with_token()` issues the credential through this service, and the login API returns the token key to the client.

The inspected authentication implementation does not evidence token expiration, token age validation, rotation on successful login, rotation after credential changes, per-device or per-session credential isolation, an absolute token lifetime, or an inactivity lifetime.

`LogoutView` explicitly deletes the authenticated user's token through `Token.objects.filter(user=request.user).delete()`.

Explicit logout therefore provides token revocation, but the broader authentication credential lifecycle remains undefined and persistent tokens can be reused across login events.

##### Audit evidence

- `SECURITY_AUDIT.md`
  - `SEC-004 — Authentication tokens are persistent and reused across login events`
  - `issue_token_for_user()`
  - `Token.objects.get_or_create(user=user)`
  - explicit logout token deletion
  - missing credential expiration and rotation controls
- `AUTHORIZATION_MATRIX.md`
  - DRF authentication includes `TokenAuthentication`
  - authenticated logout endpoint is exposed
- backend implementation
  - `accounts/services/authentication.py`
  - `accounts/views/auth.py`
  - `dental_clinic/settings.py`

##### Integrity risk

A successful login can return a previously issued persistent authentication credential instead of issuing or rotating credentials according to an explicit lifecycle policy.

If a token is compromised, subsequent successful login events do not evidence automatic invalidation or rotation of that token.

The effective credential lifetime is not bounded by a verified expiration policy.

The current one-token-per-user flow also does not evidence independent device or session credential lifecycle management.

##### Required remediation

Define and document the API authentication credential lifecycle before replacing the current implementation.

The policy must explicitly define the authentication mechanism, credential lifetime, absolute expiration, inactivity expiration where required, rotation behavior, logout revocation behavior, password-change revocation behavior, administrator-forced revocation, compromised-token response, concurrent device or session policy, and React client credential storage expectations.

Select an authentication mechanism that supports the documented lifecycle.

Persistent DRF tokens must not remain indefinitely reusable authentication state contrary to the defined credential lifecycle.

Server-side credential expiration, rotation, and security-sensitive revocation behavior must follow the verified policy.

The remediation must remain aligned with the documented architectural intention to migrate progressively toward JWT-based authentication and must explicitly define the migration or invalidation boundary for existing DRF tokens.

##### Dependencies

- AUTH-004

##### Implementation evidence

Not implemented.

##### Validation strategy

- verify successful authentication issues credentials according to the documented lifecycle,
- verify expired credentials are rejected,
- verify credential lifetime is enforced server-side,
- verify credential rotation follows the documented policy,
- verify old credentials are rejected after required rotation,
- verify logout revokes the relevant credential or session,
- verify password changes revoke credentials according to policy,
- verify administrator-forced revocation invalidates targeted credentials,
- verify concurrent device or session behavior matches the documented policy,
- verify a new login does not silently preserve a compromised credential beyond the permitted lifecycle,
- verify inactive and soft-deleted users cannot authenticate with credentials contrary to policy,
- verify the React client authentication flow matches the backend credential lifecycle,
- add authentication lifecycle regression tests,
- run `manage.py check`,
- run the full Django test suite,
- run `python3 -m compileall -q .`,
- run `git diff --check`.

##### Validation evidence

Not validated.

##### B14 freeze status

Not ready for backend contract freeze.
#### AUTH-004 — Transitional DRF authentication surface remains broader than the intended JWT architecture

**Status:** OPEN
**Priority:** P2
**Domain:** Authorization
**Remediation phase:** R7

##### Verified finding

`dental_clinic/settings.py` globally enables three DRF authentication mechanisms through `DEFAULT_AUTHENTICATION_CLASSES`:

- `TokenAuthentication`;
- `SessionAuthentication`;
- `BasicAuthentication`.

The inspected custom login flow authenticates credentials and returns a DRF token issued through the existing token-based authentication service.

The current token implementation is transitional relative to the maintainer-declared architectural intention to migrate progressively toward JWT-based authentication.

The inspected repository does not evidence a completed JWT authentication implementation or an authoritative authentication architecture contract defining the target JWT mechanism, access-token lifetime, refresh-token lifetime, refresh rotation, refresh-token revocation or blacklisting, logout semantics, password-change revocation, frontend credential storage, or the migration boundary from existing DRF tokens.

No application requirement was evidenced for globally retaining `BasicAuthentication`.

No documented React browser-session architecture requiring global `SessionAuthentication` was evidenced.

The implemented authentication surface therefore remains broader than the stated target authentication architecture.

##### Audit evidence

- `SECURITY_AUDIT.md`
  - `SEC-011 — Transitional DRF authentication surface remains broader than the intended JWT architecture`
  - global `TokenAuthentication`
  - global `SessionAuthentication`
  - global `BasicAuthentication`
  - maintainer-declared progressive JWT migration intent
  - missing authoritative JWT migration contract
- `AUTHORIZATION_MATRIX.md`
  - global DRF authentication includes Token, Session, and Basic authentication
- backend implementation
  - `dental_clinic/settings.py`
  - `accounts/services/authentication.py`
  - `accounts/views/auth.py`

##### Integrity risk

The global authentication surface exposes multiple credential-processing mechanisms with distinct security requirements and lifecycle semantics.

`BasicAuthentication` permits credentials to be presented directly through the HTTP authorization mechanism on supported endpoints.

`SessionAuthentication` introduces cookie and CSRF security requirements distinct from token or JWT authentication.

The absence of an authoritative JWT migration contract creates a risk that authentication lifecycle changes are implemented incrementally without a single verified policy governing credential issuance, lifetime, rotation, revocation, frontend storage, and migration from legacy DRF tokens.

This finding does not evidence an authorization bypass or credential disclosure.

It identifies a transitional authentication surface and an undocumented migration boundary.

##### Required remediation

Treat the JWT transition as an explicit authentication architecture migration rather than an isolated authentication-class replacement.

Define and document the target authentication contract before modifying the global authentication configuration.

The contract must explicitly define the selected JWT implementation, access-token lifetime, refresh-token lifetime, refresh-token rotation, refresh-token revocation or blacklisting, logout semantics, password-change revocation, administrator-forced revocation, concurrent device or session policy, frontend credential storage, frontend token renewal behavior, CSRF implications of the selected storage model, migration from existing DRF tokens, and removal of legacy authentication mechanisms.

Coordinate the target authentication architecture with the credential lifecycle requirements tracked by AUTH-003.

Remove global `BasicAuthentication` unless an explicit verified requirement exists.

Remove global `SessionAuthentication` unless an explicit documented browser-session requirement exists.

Remove legacy `TokenAuthentication` when the JWT migration boundary is complete.

Any temporary coexistence period must be explicitly documented with termination criteria.

##### Dependencies

- AUTH-003

##### Implementation evidence

Not implemented.

##### Validation strategy

- verify the target JWT authentication architecture is documented,
- verify access-token lifetime is enforced server-side,
- verify refresh-token lifetime follows the documented policy,
- verify refresh-token rotation follows the documented policy,
- verify revoked or blacklisted refresh credentials are rejected where required,
- verify logout follows the documented JWT lifecycle,
- verify password changes invalidate credentials according to policy,
- verify administrator-forced revocation follows the documented policy,
- verify the React client stores and renews credentials according to the documented security model,
- verify existing DRF tokens are migrated or invalidated according to the documented transition policy,
- verify `BasicAuthentication` is unavailable unless explicitly required,
- verify `SessionAuthentication` is unavailable unless explicitly required,
- verify legacy `TokenAuthentication` is removed after the migration boundary is complete,
- verify temporary authentication coexistence cannot remain indefinitely without documented justification,
- verify global `IsAuthenticated` protection remains effective on protected API endpoints,
- add authentication migration and lifecycle regression tests,
- run `manage.py check`,
- run the full Django test suite,
- run `python3 -m compileall -q .`,
- run `git diff --check`.

##### Validation evidence

Not validated.

##### B14 freeze status

Not ready for backend contract freeze.
#### FILE-001 — Clinical file upload boundaries lack evidenced file validation

**Status:** OPEN
**Priority:** P1
**Domain:** File integrity and lifecycle
**Remediation phase:** R8

##### Verified finding

The backend defines multiple clinical file storage fields, including patient attachments, imaging files, document attachments, generated document PDFs, and generated prescription PDFs.

`PatientAttachment.file`, `ImagingInstance.file`, and `DocumentAttachment.file` expose stored clinical file boundaries through Django `FileField` definitions.

The inspected clinical upload boundaries do not evidence centralized validation for maximum file size, allowed extensions, declared MIME type, actual file content or file signature, or malformed supported-file structure.

`dental_clinic/settings.py` defines media storage configuration but does not evidence an authoritative application-level clinical upload policy defining accepted file formats and bounded file sizes.

The existing file-integrity characterization tests evidence that unsafe or inconsistent upload content can reach writable API boundaries, including executable-extension uploads and MIME/extension mismatches.

For imaging records, the writable `ImagingInstanceViewSet` provides a directly evidenced API upload boundary.

The repository also defines `DICOMConfiguration`, but the inspected upload boundary does not evidence a dedicated DICOM validation policy or DICOM structural validation.

##### Audit evidence

- `SECURITY_AUDIT.md`
  - `SEC-002 — Clinical file upload boundaries lack evidenced file validation`
  - missing size validation
  - missing extension validation
  - missing MIME-type validation
  - missing file-signature or magic-byte validation
  - missing malformed-file rejection where structural validation is required
  - missing dedicated DICOM validation policy where DICOM is supported
- backend models
  - `patients/models.py::PatientAttachment.file`
  - `imaging/models.py::ImagingInstance.file`
  - `documents/models.py::DocumentAttachment.file`
  - `documents/models.py::Document.pdf_file`
  - `prescriptions/models.py::Prescription.pdf_file`
  - `imaging/models.py::DICOMConfiguration`
- characterization tests
  - `accounts/tests/test_file_integrity_audit.py`
  - executable-extension upload acceptance
  - MIME and extension mismatch acceptance
- media configuration
  - `dental_clinic/settings.py`

##### Integrity risk

A client reaching a writable clinical upload boundary may submit a file whose size, filename extension, declared MIME type, or actual content does not match the intended clinical file policy.

Filename and client-declared MIME metadata are not sufficient evidence of actual file content.

Without content-signature or structural validation where required, malformed or disguised files may be stored as clinical records.

For medical imaging formats, generic file acceptance does not establish that uploaded content is valid DICOM or another explicitly supported imaging format.

This finding does not claim that malicious content has been uploaded.

It identifies the absence of evidenced preventive validation at clinical file ingestion boundaries.

##### Required remediation

Define and document a centralized clinical file upload policy before modifying individual models, serializers, or views.

The policy must explicitly define allowed file categories per clinical boundary, maximum file size, allowed extensions, declared MIME-type validation, actual content or file-signature validation, malformed-file rejection requirements, storage naming and path requirements, duplicate-file handling, replacement behavior, deletion behavior, rejected-upload audit requirements, and DICOM-specific validation if DICOM upload is supported.

Apply reusable validation controls consistently to writable patient attachment, imaging, and document attachment boundaries.

Generated server-side PDF fields must be distinguished from client-controlled upload boundaries and validated according to their actual lifecycle.

Do not rely solely on filename extensions or client-declared MIME types as evidence of file content.

Define a dedicated validation policy for DICOM or other medical imaging formats if those formats remain supported.

Rejected uploads must not create valid clinical domain records and must produce audit evidence according to the documented policy.

##### Dependencies

None.

##### Implementation evidence

Not implemented.

##### Validation strategy

- verify files within the documented size limit are accepted,
- verify oversized files are rejected,
- verify allowed extensions are accepted according to boundary policy,
- verify forbidden extensions are rejected,
- verify extension and declared MIME mismatches are rejected,
- verify declared MIME type and actual content mismatches are rejected,
- verify file-signature or content validation follows the documented policy,
- verify malformed supported files are rejected where structural validation is required,
- verify rejected uploads do not create valid clinical domain records,
- verify rejected upload attempts produce the required audit evidence,
- verify patient attachment upload validation,
- verify imaging upload validation,
- verify document attachment upload validation,
- verify generated server-side PDFs remain functional under their defined lifecycle,
- verify DICOM-specific validation if DICOM upload remains supported,
- add clinical upload security regression tests,
- run `manage.py check`,
- run the full Django test suite,
- run `python3 -m compileall -q .`,
- run `git diff --check`.

##### Validation evidence

Not validated.

##### B14 freeze status

Not ready for backend contract freeze.
#### SEC-001 — Production Django transport and cookie security policy is not evidenced

**Status:** OPEN
**Priority:** P1
**Domain:** Security configuration and operational hardening
**Remediation phase:** R11

##### Verified finding

The inspected Django settings do not define an explicit production transport and cookie security policy.

The repository does not evidence configuration for `SECURE_SSL_REDIRECT`, `SECURE_HSTS_SECONDS`, `SECURE_HSTS_INCLUDE_SUBDOMAINS`, `SECURE_HSTS_PRELOAD`, `SESSION_COOKIE_SECURE`, `CSRF_COOKIE_SECURE`, or `SECURE_PROXY_SSL_HEADER`.

Repository inspection does not evidence an alternative production settings module defining equivalent controls.

The repository also does not evidence a separate production deployment definition selecting the available production application-server path together with an HTTPS reverse proxy and documented transport security controls.

No authoritative production deployment policy was evidenced defining TLS termination, trusted reverse proxy boundaries, HTTPS redirect ownership, HSTS ownership, secure cookie requirements, or original-request scheme handling behind a proxy.

This finding does not claim that a deployed production instance currently serves plain HTTP traffic.

It identifies the absence of a repository-evidenced production transport and cookie security policy.

##### Audit evidence

- `SECURITY_AUDIT.md`
  - `SEC-005 — Production Django transport and cookie security policy is not evidenced`
  - missing explicit HTTPS redirect policy
  - missing HSTS policy
  - missing secure session-cookie policy
  - missing secure CSRF-cookie policy
  - missing trusted proxy and original HTTPS scheme policy
  - missing repository-evidenced production deployment boundary
- backend configuration
  - `dental_clinic/settings.py`
  - absence of `SECURE_SSL_REDIRECT`
  - absence of `SECURE_HSTS_SECONDS`
  - absence of `SECURE_HSTS_INCLUDE_SUBDOMAINS`
  - absence of `SECURE_HSTS_PRELOAD`
  - absence of `SESSION_COOKIE_SECURE`
  - absence of `CSRF_COOKIE_SECURE`
  - absence of `SECURE_PROXY_SSL_HEADER`

##### Integrity risk

The repository does not prove that a production deployment will enforce HTTPS redirection, secure cookie transport, or HTTP Strict Transport Security.

If the current settings are reused in production without an external documented control layer, transport security can depend on undocumented infrastructure behavior.

Session and CSRF cookies are not repository-evidenced as restricted to secure HTTPS transport.

The application also does not evidence how Django determines the original HTTPS request scheme when deployed behind a trusted reverse proxy.

Incorrect proxy trust configuration can allow forwarding metadata to influence request-scheme interpretation outside the intended deployment trust boundary.

##### Required remediation

Define and document the production deployment trust boundary before enabling transport security settings.

The policy must explicitly define TLS termination, the trusted reverse proxy architecture, authoritative forwarded protocol handling, HTTPS redirect ownership, HSTS ownership and duration, secure session-cookie requirements, secure CSRF-cookie requirements, development and production settings separation, and production application-server requirements.

Create an explicit production settings boundary or equivalent environment-driven security policy.

Enforce HTTPS redirection at the documented layer.

Enable secure session and CSRF cookies in production.

Configure HSTS only after complete HTTPS coverage is verified.

Configure `SECURE_PROXY_SSL_HEADER` only when a trusted reverse proxy strips attacker-controlled forwarded protocol headers and sets the authoritative protocol value according to the documented trust model.

Production execution must use a supported WSGI or ASGI application server rather than Django `runserver`.

Development settings must remain usable without silently weakening the production security policy.

##### Dependencies

None.

##### Implementation evidence

Not implemented.

##### Validation strategy

- verify production `DEBUG` is disabled,
- verify production HTTPS requests are recognized correctly by Django,
- verify HTTP requests are redirected according to the documented HTTPS ownership policy,
- verify session cookies carry the `Secure` attribute in production,
- verify CSRF cookies carry the `Secure` attribute in production,
- verify HSTS is emitted according to the documented production policy,
- verify HSTS is not enabled before complete HTTPS coverage is established,
- verify forwarded protocol headers are trusted only through the documented proxy boundary,
- verify attacker-controlled forwarding headers cannot independently mark an insecure request as trusted HTTPS,
- verify the production process does not use Django `runserver`,
- verify development settings remain usable,
- run Django deployment checks against the production configuration,
- add production security configuration regression tests,
- run `manage.py check`,
- run the full Django test suite,
- run `python3 -m compileall -q .`,
- run `git diff --check`.

##### Validation evidence

Not validated.

##### B14 freeze status

Not ready for backend contract freeze.
#### SEC-002 — Django can start with a known static SECRET_KEY fallback

**Status:** OPEN
**Priority:** P1
**Domain:** Security configuration and operational hardening
**Remediation phase:** R11

##### Verified finding

`dental_clinic/settings.py` obtains `SECRET_KEY` through environment-driven configuration but defines the known static fallback value `changeme`.

The application can therefore start when the `SECRET_KEY` runtime configuration is absent.

`docker-compose.yml` injects `SECRET_KEY` from the environment into the web service, but this does not eliminate the fallback behavior implemented by the Django settings module.

Application execution outside the inspected Compose environment, or execution with incomplete runtime configuration, can fall back to the known static key.

The repository root `.env.example` documents the placeholder value `replace-me` and does not evidence a committed production secret.

This finding does not claim that a currently running development or production environment uses `changeme`.

It identifies that Django startup does not require a deployment-provided secret because the settings module accepts a known static fallback.

##### Audit evidence

- `SECURITY_AUDIT.md`
  - `SEC-006 — Django can start with a known static SECRET_KEY fallback`
  - environment-driven `SECRET_KEY`
  - static `changeme` fallback
  - Compose environment injection does not remove settings fallback behavior
  - production secret provisioning and rotation requirements
- backend configuration
  - `dental_clinic/settings.py`
  - `SECRET_KEY = env('SECRET_KEY', default='changeme')`
  - `dental_clinic/asgi.py`
  - `dental_clinic/wsgi.py`
- environment configuration
  - `docker-compose.yml`
  - `.env.example`
  - `SECRET_KEY=replace-me`
- false-positive clarification
  - `SEC-FP-001 — .env.example does not contain an observed production secret`

##### Integrity risk

Django cryptographic signing security depends on `SECRET_KEY` remaining secret and unpredictable.

A known static fallback creates a configuration state in which the application can start with a predictable signing secret.

Environment injection through one deployment path does not enforce secret provisioning across every supported application startup path.

If the fallback is used, cryptographic operations relying on the Django secret key can operate with a publicly known value.

The absence of an authoritative secret provisioning and rotation policy also leaves development, test, and production secret lifecycle boundaries undefined.

##### Required remediation

Make `SECRET_KEY` a mandatory runtime secret.

Remove the static `changeme` fallback from Django settings.

Application startup must fail when the required secret is absent.

Define secret provisioning separately for development, test, and production environments.

Development convenience must not create a production-capable startup path using a known fallback secret.

Define and document the production secret provisioning mechanism, secret rotation procedure, and operational impact of rotation on Django-signed application data.

Keep environment-specific secret values outside version control.

##### Dependencies

None.

##### Implementation evidence

Not implemented.

##### Validation strategy

- verify application startup fails when `SECRET_KEY` is absent,
- verify a deployment-provided `SECRET_KEY` permits application startup,
- verify no known static fallback remains in Django settings,
- verify development secret provisioning follows the documented development policy,
- verify test secret provisioning follows the documented test policy,
- verify production configuration requires an externally provisioned secret,
- verify `.env.example` contains placeholder material only,
- verify environment-specific secret values remain excluded from version control,
- verify the production secret rotation procedure is documented,
- verify the rotation procedure documents the impact on Django-signed application data,
- run Django deployment checks against the production configuration,
- add secret configuration regression tests,
- run `manage.py check`,
- run the full Django test suite,
- run `python3 -m compileall -q .`,
- run `git diff --check`.

##### Validation evidence

Not validated.

##### B14 freeze status

Not ready for backend contract freeze.
#### SEC-003 — Backend container does not enforce a non-root runtime identity

**Status:** OPEN
**Priority:** P1
**Domain:** Security configuration and operational hardening
**Remediation phase:** R11

##### Verified finding

The repository root `Dockerfile` builds the backend image from `python:3.12-slim`.

The Dockerfile does not create a dedicated application user or group and does not define a `USER` instruction before the backend entrypoint or application command.

The backend image therefore does not evidence an explicit non-root runtime identity.

`docker/entrypoint.sh` executes the PostgreSQL availability check, Django migrations, static collection, and the final application process without an evidenced privilege-drop mechanism.

`docker-compose.yml` does not define an explicit `user` for the `web` service.

The inspected `web` service also does not evidence `cap_drop`, `security_opt` with `no-new-privileges`, or a read-only root filesystem.

The development Compose configuration bind-mounts the repository root into `/app` and mounts `media_data` at `/app/media`.

The Compose `web` service overrides the image Gunicorn command with Django `runserver`.

Repository inspection does not evidence an alternative backend container definition enforcing a dedicated runtime user.

##### Audit evidence

- `SECURITY_AUDIT.md`
  - `SEC-008 — Backend container does not enforce a non-root runtime identity`
  - missing dedicated backend application user and group
  - missing Dockerfile `USER`
  - missing privilege-drop mechanism
  - missing Compose `web.user`
  - missing capability and privilege-escalation restrictions
  - development repository bind mount
- backend container
  - `Dockerfile`
  - base image `python:3.12-slim`
  - `docker/entrypoint.sh`
  - image command uses Gunicorn
- Compose runtime
  - `docker-compose.yml`
  - `web` service has no explicit runtime user
  - repository root bind-mounted at `/app`
  - `media_data` mounted at `/app/media`
  - Compose command overrides Gunicorn with Django `runserver`

##### Integrity risk

The backend container does not prove least-privilege execution at the operating-system identity boundary.

If an application-level compromise reaches operating-system execution inside the container, the compromised process can inherit the container's default elevated identity and broader filesystem access than a dedicated application user should require.

The development repository bind mount also exposes the mounted application tree to the container process according to host and Docker mount permissions.

The absence of explicit capability, privilege-escalation, and filesystem restrictions leaves the container runtime hardening boundary undefined.

This finding does not claim container escape, host compromise, or an existing remote code execution vulnerability.

It identifies the absence of repository-evidenced container least-privilege controls.

##### Required remediation

Define separate development and production container privilege requirements before modifying the backend image.

The policy must explicitly define the runtime user and group, required filesystem ownership, writable application paths, media storage permissions, static collection ownership, migration execution ownership, bind-mount policy, Linux capability requirements, privilege-escalation restrictions, and read-only filesystem feasibility.

Create a dedicated non-root application user and group in the backend image.

Assign only required application paths to that identity and run the normal backend application process as the dedicated non-root user.

Verify migration and static collection execution according to the documented deployment policy without requiring broad root runtime privileges.

Separate development bind-mount behavior from the production container configuration.

Drop unnecessary Linux capabilities where supported.

Enable `no-new-privileges` where compatible with the documented deployment model.

Evaluate a read-only root filesystem with explicit writable mounts for required runtime data.

Coordinate production application-server execution with the production deployment boundary tracked by SEC-001.

##### Dependencies

- SEC-001

##### Implementation evidence

Not implemented.

##### Validation strategy

- verify the backend application process runs as a non-root UID,
- verify the application starts successfully with the dedicated runtime identity,
- verify database migrations execute according to the documented deployment policy,
- verify static collection executes according to the documented deployment policy,
- verify required media paths remain writable,
- verify application source paths are not writable in production unless explicitly required,
- verify unnecessary Linux capabilities are removed according to policy,
- verify privilege escalation is restricted according to policy,
- verify development bind mounts are not silently inherited by the production deployment definition,
- verify container restart and deployment workflows remain functional,
- verify the production image does not require root privileges for normal application request handling,
- add container runtime security regression validation,
- run `manage.py check`,
- run the full Django test suite,
- run `python3 -m compileall -q .`,
- run `git diff --check`.

##### Validation evidence

Not validated.

##### B14 freeze status

Not ready for backend contract freeze.
#### SEC-004 — Python dependencies are not reproducibly locked

**Status:** OPEN
**Priority:** P1
**Domain:** Security configuration and operational hardening
**Remediation phase:** R11

##### Verified finding

The repository root `requirements.txt` is the only evidenced Python dependency declaration or resolution artifact.

It declares `Django>=4.2`, `psycopg2-binary`, `django-environ`, `djangorestframework`, and `django-cors-headers==4.8.0`.

Only `django-cors-headers` is pinned to an exact version.

The Django dependency uses the open-ended lower-bound constraint `Django>=4.2`.

`psycopg2-binary`, `django-environ`, and `djangorestframework` do not define version constraints.

Repository inspection does not evidence a Python lock file or constraints file containing a complete exact resolved dependency set.

The backend `Dockerfile` installs dependencies directly from `requirements.txt` and additionally installs `gunicorn` without an exact version constraint.

Independent backend builds from the same repository commit are therefore not repository-evidenced as resolving identical direct and transitive Python package versions.

##### Audit evidence

- `SECURITY_AUDIT.md`
  - `SEC-009 — Python dependencies are not reproducibly locked`
  - open-ended Django version constraint
  - unconstrained runtime dependencies
  - missing complete resolved dependency lock
  - backend image installs from unresolved dependency declarations
- dependency declaration
  - `requirements.txt`
  - `Django>=4.2`
  - `psycopg2-binary`
  - `django-environ`
  - `djangorestframework`
  - `django-cors-headers==4.8.0`
- backend container
  - `Dockerfile`
  - `RUN pip install --no-cache-dir -r requirements.txt gunicorn`
  - unconstrained `gunicorn` installation
- repository dependency artifacts
  - no evidenced `constraints*.txt`
  - no evidenced `pyproject.toml`
  - no evidenced `poetry.lock`
  - no evidenced `Pipfile.lock`
  - no evidenced `uv.lock`

##### Integrity risk

Backend builds can resolve different dependency versions without a repository change.

A newly published direct or transitive dependency version can alter application behavior, compatibility, or security characteristics between builds.

The open-ended Django constraint permits later framework versions to participate in dependency resolution without an explicit repository change selecting the exact resolved version.

Installing `gunicorn` separately without a version constraint introduces an additional unresolved production runtime dependency outside the declared `requirements.txt` dependency set.

This weakens build reproducibility, incident investigation, rollback confidence, dependency drift detection, and vulnerability remediation traceability.

This finding does not claim that an installed dependency is currently vulnerable.

It identifies the absence of a reproducible Python dependency resolution policy and exact resolved dependency set.

##### Required remediation

Define and document a Python dependency management and locking policy before replacing the current dependency declarations.

The policy must explicitly define direct dependency declaration, exact resolved dependency locking, transitive dependency capture, lock regeneration procedure, dependency update review, security advisory review, development dependency handling, production dependency handling, production application-server dependency declaration, and automated dependency update policy.

Choose a supported dependency locking workflow.

Separate human-maintained direct dependency declarations from the complete resolved dependency set where the selected workflow requires that distinction.

Generate and commit a complete exact-version dependency lock or equivalent constraints artifact.

Declare Gunicorn through the authoritative dependency workflow rather than installing an unconstrained production dependency separately in the Dockerfile.

Make backend image builds consume the complete resolved dependency set.

Document the controlled lock regeneration and dependency update process.

Add dependency vulnerability review and unintended dependency drift detection to the maintenance or CI workflow.

##### Dependencies

None.

##### Implementation evidence

Not implemented.

##### Validation strategy

- verify direct Python dependencies are explicitly declared,
- verify every resolved production dependency has an exact reviewed version,
- verify transitive dependencies are captured by the selected locking workflow,
- verify Django resolves to an intentional reviewed version,
- verify Gunicorn is declared through the authoritative dependency workflow,
- verify production image builds consume the locked dependency set,
- verify two clean backend builds from the same commit resolve identical Python package versions,
- verify lock regeneration is documented and intentional,
- verify dependency updates produce a reviewable repository diff,
- verify known vulnerability review is part of the dependency update workflow,
- verify CI or equivalent validation detects unintended dependency drift,
- verify rollback to a previous commit restores the previous resolved dependency set,
- add dependency reproducibility regression validation,
- run `manage.py check`,
- run the full Django test suite,
- run `python3 -m compileall -q .`,
- run `git diff --check`.

##### Validation evidence

Not validated.

##### B14 freeze status

Not ready for backend contract freeze.
#### SEC-005 — Development database credentials and PostgreSQL host exposure are embedded in Compose configuration

**Status:** OPEN
**Priority:** P1
**Domain:** Security configuration and operational hardening
**Remediation phase:** R11

##### Verified finding

`docker-compose.yml` publishes the PostgreSQL service to the Docker host through the `5432:5432` port mapping.

The same Compose definition configures the database with the repository-known values `POSTGRES_DB: dental`, `POSTGRES_USER: dental`, and `POSTGRES_PASSWORD: dental`.

The inspected Compose network already permits the `web` service to reach PostgreSQL through the internal service name `db`.

Repository inspection does not evidence that PostgreSQL host publication is required for normal backend-to-database communication.

`dental_clinic/settings.py` obtains the application database configuration through the environment-backed `DATABASE_URL`.

The Django settings module is therefore not evidenced as hardcoding the database password in Python configuration.

The repository root `.env.example` documents placeholder database connection material and includes a commented Docker connection example using the known development credentials.

Repository inspection does not evidence a separate production Compose or deployment definition defining a distinct database exposure and credential provisioning policy.

This finding does not claim that production database credentials are committed to the repository.

It identifies repository-known development database credentials, unnecessary or undocumented PostgreSQL host exposure, and the absence of a repository-evidenced production database deployment boundary.

##### Audit evidence

- `SECURITY_AUDIT.md`
  - `SEC-010 — Development database credentials and PostgreSQL host exposure are embedded in Compose`
  - PostgreSQL host publication through `5432:5432`
  - repository-known development database credentials
  - internal backend-to-database container network path
  - missing separate production database exposure policy
- Compose configuration
  - `docker-compose.yml`
  - `POSTGRES_DB: dental`
  - `POSTGRES_USER: dental`
  - `POSTGRES_PASSWORD: dental`
  - host port mapping `5432:5432`
  - `web` service reaches PostgreSQL through the Compose network
- backend configuration
  - `dental_clinic/settings.py`
  - environment-backed `DATABASE_URL`
  - PostgreSQL requirement validation
- environment example
  - `.env.example`
  - placeholder local PostgreSQL connection example
  - commented Docker connection example using `dental:dental`
- deployment configuration
  - no evidenced separate production Compose or deployment definition

##### Integrity risk

The development PostgreSQL service is published to the Docker host while using repository-known credentials.

On a host where the published database port is reachable by untrusted systems, the PostgreSQL attack surface is broader than required for normal communication between the backend and database containers.

Reusing the inspected Compose configuration or known development credentials outside an isolated development environment would create a materially unsafe database deployment boundary.

The absence of an authoritative development and production database exposure policy leaves host access requirements, credential provisioning, credential rotation, database role privilege scope, and administrative access boundaries undefined.

This finding does not claim that the current PostgreSQL service is internet-accessible.

Actual network reachability depends on the Docker host, firewall, and surrounding infrastructure, which were not inspected.

##### Required remediation

Define and document separate development and production database exposure policies before modifying the Compose database configuration.

The policy must explicitly define whether PostgreSQL requires host access, allowed database network boundaries, development credential handling, production credential provisioning, credential rotation, database user privilege scope, backup access requirements, and administrative access requirements.

Remove PostgreSQL host port publication where host access is not required.

Keep normal backend-to-database communication on the internal container network.

Externalize database credentials from tracked Compose configuration and require explicit credential provisioning according to the documented environment policy.

Prevent repository-known development credentials from being accepted by the production deployment policy.

Define a least-privilege PostgreSQL application role.

Separate normal application database credentials from administrative database credentials.

Document controlled host access when local database administration requires direct PostgreSQL access.

Coordinate the production database deployment boundary with the production configuration policy tracked by SEC-001 and the mandatory secret provisioning policy tracked by SEC-002.

Add deployment configuration regression validation.

##### Dependencies

- SEC-001
- SEC-002

##### Implementation evidence

Not implemented.

##### Validation strategy

- verify the backend reaches PostgreSQL through the documented internal container network path,
- verify PostgreSQL is not published to the host when host access is unnecessary,
- verify any documented development host access is explicitly controlled,
- verify database credentials are explicitly provisioned outside tracked Compose configuration,
- verify repository-known development credentials are rejected by production policy,
- verify the application uses a dedicated PostgreSQL application role,
- verify the application database role has only documented required privileges,
- verify administrative database credentials are not used by normal application requests,
- verify production database credentials are absent from version control,
- verify database credential rotation is documented,
- verify development database workflows remain functional according to the documented exposure policy,
- add deployment database configuration regression validation,
- run `manage.py check`,
- run the full Django test suite,
- run `python3 -m compileall -q .`,
- run `git diff --check`.

##### Validation evidence

Not validated.

##### B14 freeze status

Not ready for backend contract freeze.
#### SEC-006 — Frontend dependency lockfiles are explicitly excluded from version control

**Status:** OPEN
**Priority:** P2
**Domain:** Security configuration and operational hardening
**Remediation phase:** R11

##### Verified finding

The repository root `.gitignore` explicitly ignores `package-lock.json`, `yarn.lock`, and `pnpm-lock.yaml`.

The React frontend is npm-based.

`frontend/package.json` defines the frontend dependency manifest and uses compatible-version ranges for direct and development dependencies.

`frontend/package-lock.json` currently exists and is already tracked by Git.

The tracked npm lockfile therefore provides repository-controlled dependency resolution at the inspected repository state.

However, the root ignore policy remains inconsistent with the selected npm workflow because it explicitly excludes `package-lock.json`.

A newly generated npm lockfile at another repository path would be ignored by the current generic rule unless explicitly tracked or force-added.

`frontend/Dockerfile` copies `package*.json` but installs dependencies with `npm install` rather than the lockfile-enforcing `npm ci` workflow.

Repository inspection does not evidence an authoritative frontend package-manager and dependency-locking policy defining npm as the selected package manager, the required tracked lockfile, deterministic installation requirements, dependency update procedure, or lockfile drift validation.

This finding does not claim that `frontend/package-lock.json` is currently absent from version control.

It identifies a contradictory repository ignore policy, non-deterministic container installation command, and missing authoritative frontend dependency-locking contract.

##### Audit evidence

- `SECURITY_AUDIT.md`
  - `SEC-012 — Frontend dependency lockfiles are explicitly excluded from version control`
  - root lockfile ignore rules
  - npm frontend dependency manifest
  - compatible-version dependency ranges
  - frontend container uses `npm install`
- repository ignore policy
  - `.gitignore`
  - `package-lock.json`
  - `yarn.lock`
  - `pnpm-lock.yaml`
- frontend dependency manifest
  - `frontend/package.json`
  - npm package manifest
  - caret dependency constraints
- frontend dependency lock
  - `frontend/package-lock.json`
  - exists on disk
  - already tracked by Git
- frontend container build
  - `frontend/Dockerfile`
  - `COPY package*.json ./`
  - `RUN npm install`
- dependency installation references
  - repository-owned frontend Dockerfile uses `npm install`
  - inspected additional `npm install` references under `frontend/node_modules` belong to installed third-party package metadata and do not establish project build policy

##### Integrity risk

The repository currently contains a tracked npm lockfile, but its root ignore policy communicates that npm lockfiles are not intended to be version-controlled.

This creates a contradictory dependency-management contract and increases the risk that future lockfile creation, regeneration, relocation, or recovery workflows silently produce ignored dependency-resolution state.

The frontend container build uses `npm install`, which may modify or reconcile dependency resolution instead of requiring exact installation from the committed lockfile.

As a result, automated or container dependency installation is not evidenced as enforcing the committed dependency tree as an immutable build input.

The absence of an authoritative frontend dependency-locking policy also leaves package-manager selection, lockfile ownership, controlled dependency updates, vulnerability review, and installation drift detection undefined.

This finding does not claim that the currently tracked frontend dependency tree is known to contain a vulnerable package.

##### Required remediation

Define npm as the authoritative frontend package manager unless repository architecture explicitly selects another package manager before remediation.

Document the authoritative frontend dependency-locking policy.

Retain `frontend/package-lock.json` in version control.

Remove the generic `package-lock.json` ignore rule from `.gitignore`.

Keep unused package-manager lockfiles excluded where appropriate unless the selected package-manager policy changes.

Require deterministic npm installation from the committed lockfile for automated and container builds.

Replace `npm install` with `npm ci` in the frontend container build where the committed lockfile is the authoritative dependency-resolution input.

Define a controlled dependency update procedure requiring review of both `frontend/package.json` and `frontend/package-lock.json`.

Document frontend dependency vulnerability review as part of the maintenance workflow.

Add validation capable of detecting frontend dependency installation or lockfile drift.

##### Dependencies

None identified.

##### Implementation evidence

Not implemented.

##### Validation strategy

- verify npm is documented as the authoritative frontend package manager,
- verify `frontend/package-lock.json` is tracked by Git,
- verify the selected npm lockfile is not excluded by repository ignore policy,
- verify unused package-manager lockfiles remain excluded according to policy,
- verify frontend container builds consume the committed lockfile,
- verify automated npm installation uses `npm ci`,
- verify two clean frontend installations from the same commit resolve the same dependency tree,
- verify dependency updates produce reviewable `frontend/package.json` and `frontend/package-lock.json` diffs,
- verify transitive dependency changes are visible in the committed lockfile,
- verify frontend dependency vulnerability review is documented,
- verify rollback to a previous commit restores the previous resolved frontend dependency set,
- verify dependency installation or lockfile drift is detected by automated validation,
- run the frontend production build,
- run `manage.py check`,
- run the full Django test suite,
- run `python3 -m compileall -q .`,
- run `git diff --check`.

##### Validation evidence

Not validated.

##### B14 freeze status

Not ready for backend contract freeze.
