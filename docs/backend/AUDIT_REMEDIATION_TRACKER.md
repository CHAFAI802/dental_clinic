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
| R4 | Transactional workflow services |
| R5 | Billing integrity |
| R6 | State machines |
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
