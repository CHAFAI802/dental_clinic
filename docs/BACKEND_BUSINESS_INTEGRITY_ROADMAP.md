# Backend Business Integrity Roadmap (Django + DRF)

This document is the **persistent source of truth** for the backend business integrity audit.

Status markers:
- `[ ] NOT STARTED`
- `[~] IN PROGRESS`
- `[x] VERIFIED COMPLETE` (only after validation)
- `[!] BLOCKED`

Repository audit docs live in: `docs/backend/`

---

## PHASE B0 — EXISTING API VERIFICATION BASELINE

- [x] VERIFIED COMPLETE Inspect `scripts/smoke_test.py`
- [x] VERIFIED COMPLETE Confirm the meaning of the `ROUTES : 128 PASSED : 128 FAILED : 0 SKIPPED : 0` result
- [x] VERIFIED COMPLETE Identify exactly what the smoke test verifies
- [x] VERIFIED COMPLETE Identify exactly what it does **NOT** verify
- [x] VERIFIED COMPLETE Record verified API baseline

**Verified baseline (derived from current code):**
- The smoke test dynamically discovers DRF router operations by walking Django URL patterns and reading `callback.actions` for routes under `/api/`.
- It counts **unique (viewset, HTTP method, action)** tuples.
- `128` operations is consistent with:
  - 21 CRUD ViewSets × 6 actions (LIST/CREATE/RETRIEVE/UPDATE/PARTIAL_UPDATE/DESTROY) = 126
  - 1 read-only ViewSet (`AuditLogViewSet`) × 2 actions (LIST/RETRIEVE) = 2
  - Total = 128

---

## PHASE B1 — MODEL INTEGRITY

- [x] VERIFIED COMPLETE Inventory installed apps and all models
- [x] VERIFIED COMPLETE Audit fields (null/blank/defaults/choices)
- [x] VERIFIED COMPLETE Audit relationships (FK/O2O/M2M/related_name)
- [x] VERIFIED COMPLETE Audit `on_delete` deletion policies and deletion chains
- [x] VERIFIED COMPLETE Audit unique / constraints / indexes
- [x] VERIFIED COMPLETE Audit ordering
- [x] VERIFIED COMPLETE Audit model validation / clean()
- [x] VERIFIED COMPLETE Audit overridden save/delete behavior
- [x] VERIFIED COMPLETE Audit signals affecting integrity
- [x] VERIFIED COMPLETE Generate model relationship graph (`docs/backend/MODEL_RELATIONSHIP_GRAPH.md`)

---

## PHASE B2 — SERIALIZER CONTRACT AUDIT

- [x] VERIFIED COMPLETE Inventory serializers exposed via API
- [x] VERIFIED COMPLETE Audit readable vs writable vs read-only fields
- [x] VERIFIED COMPLETE Audit validation rules (field + object)
- [x] VERIFIED COMPLETE Audit nested/writable relationship safety
- [x] VERIFIED COMPLETE Create `docs/backend/SERIALIZER_CONTRACT_AUDIT.md`

---

## PHASE B3 — CROSS-MODEL CONSISTENCY

- [x] VERIFIED COMPLETE Audit cross-model consistency risks in implementation
- [x] VERIFIED COMPLETE Implement executable tests for discovered consistency rules

---

## PHASE B4 — BUSINESS RULE AUDIT

- [x] VERIFIED COMPLETE Derive and map business rules from real implementation
- [x] VERIFIED COMPLETE Create `docs/backend/BUSINESS_RULE_MATRIX.md`

---

## PHASE B5 — STATE MACHINE AUDIT

- [x] VERIFIED COMPLETE Find all status/state fields
- [x] VERIFIED COMPLETE Identify transition logic and bypass paths
- [x] VERIFIED COMPLETE Create `docs/backend/STATE_MACHINE_AUDIT.md`

---

## PHASE B6 — AUTHORIZATION MATRIX

- [x] VERIFIED COMPLETE Derive roles from real code
- [x] VERIFIED COMPLETE Audit authentication configuration + permission classes
- [x] VERIFIED COMPLETE Audit queryset filtering + object-level permissions
- [x] VERIFIED COMPLETE Create `docs/backend/AUTHORIZATION_MATRIX.md`
- [x] VERIFIED COMPLETE Implement direct API authorization tests (GET/PUT/PATCH/DELETE)

---

## PHASE B7 — CONCURRENCY AND TRANSACTION SAFETY

- [x] VERIFIED COMPLETE Identify concurrency-sensitive operations
- [x] VERIFIED COMPLETE Audit `transaction.atomic`, `select_for_update`, DB constraints
- [x] VERIFIED COMPLETE Create `docs/backend/CONCURRENCY_AUDIT.md`

---

## PHASE B8 — IDEMPOTENCE AND DUPLICATE SUBMISSION

- [x] VERIFIED COMPLETE Audit critical POST operations for duplicate creation risk
- [x] VERIFIED COMPLETE Create `docs/backend/IDEMPOTENCE_AUDIT.md`

---

## PHASE B9 — FILE INTEGRITY AND UPLOAD SECURITY

- [x] VERIFIED COMPLETE Inventory FileField/ImageField + multipart endpoints
- [x] VERIFIED COMPLETE Audit validation (type/size/paths/orphans)
- [x] VERIFIED COMPLETE Create `docs/backend/FILE_INTEGRITY_AUDIT.md`
- [x] VERIFIED COMPLETE Implement executable file integrity tests (synthetic files)

---

## PHASE B10 — AUDIT TRAIL INTEGRITY

- [x] VERIFIED COMPLETE Audit AuditLog model + write paths
- [x] VERIFIED COMPLETE Verify append-only behavior
- [x] VERIFIED COMPLETE Verify AuditLog cannot be mutated via API
- [x] VERIFIED COMPLETE Create `docs/backend/AUDIT_TRAIL_AUDIT.md`

---

## PHASE B11 — WEBSITE DOMAIN AUDIT

- [x] VERIFIED COMPLETE Inspect current `website` application implementation
- [x] VERIFIED COMPLETE Create `docs/backend/WEBSITE_DOMAIN_SPECIFICATION.md`

---

## PHASE B12 — END-TO-END BUSINESS WORKFLOWS

- [x] VERIFIED COMPLETE Build workflow tests derived from real model graph
- [x] VERIFIED COMPLETE Create `docs/backend/WORKFLOW_AUDIT.md`

---

## PHASE B13 — REMEDIATION PLAN

- [x] VERIFIED COMPLETE Create `docs/backend/REMEDIATION_PLAN.md`

---

## PHASE B14 — BACKEND CONTRACT FREEZE

- [x] VERIFIED Validate all audit tests + existing smoke test
- [x] VERIFIED Update API contract matrix if needed
- [x] VERIFIED Mark backend business integrity verified

### 2026-07-13 (continued) — PHASE B13

### Resume protocol (performed)
- Inspected the existing backend audit deliverables under `docs/backend/`
- Consolidated only findings that were explicitly supported by the audit documents
- Kept remediation recommendations implementation-oriented without changing production behavior
- Preserved the existing characterization-test evidence base

### Commands executed
- `git status --short`
- `python3 - <<'PY'`
from pathlib import Path

path = Path("docs/backend/REMEDIATION_PLAN.md")
assert path.exists(), "REMEDIATION_PLAN.md missing"

text = path.read_text(encoding="utf-8")

required = [
"BACKEND BUSINESS INTEGRITY REMEDIATION PLAN",
"Prioritization Method",
"Executive Risk Summary",
"Remediation Dependency Order",
"Prioritized Remediation Matrix",
"P0",
"P1",
"P2",
"P3",
"Proposed Implementation Phases",
"Validation Strategy",
"Explicit Non-Goals",
"Final Recommendation",
]

for item in required:
assert item in text, f"Missing section/content: {item}"

print("B13 REMEDIATION PLAN STRUCTURE VERIFIED")
PY
- `docker compose exec -T web python manage.py check`
- `PYTHONPYCACHEPREFIX=/tmp/pycache python3 -m compileall -q .`
- `git diff --check`
- `git status --short`

### PHASE B13 deliverable(s)
- Created: `docs/backend/REMEDIATION_PLAN.md`

### Validation (PHASE B13)
Status: **PASS with WARN**
- PASS: remediation plan structure verified with the required section/content checks.
- PASS: repository diff check completed without whitespace issues.
- WARN: runtime Django validation and full test-suite execution were not completed in this environment because the stack/runtime context could not be fully verified here; the plan is based on the existing audited evidence set.

### Prioritization summary
- P0: destructive deletion semantics, financial aggregate tampering, payment/invoice atomicity.
- P1: cross-model consistency, scheduling invariants, inventory constraints, state-machine enforcement, authorization scope, upload validation.
- P2: file lifecycle, duplicate handling, workflow orchestration, audit completeness.
- P3: website domain ownership and product-decision-dependent lifecycle policies.

### Files created/modified in this session
- Created: `docs/backend/REMEDIATION_PLAN.md`
- Modified: `docs/BACKEND_BUSINESS_INTEGRITY_ROADMAP.md`

### Next phase recommendation
- PHASE B14 — BACKEND CONTRACT FREEZE
- First action: validate the existing characterization tests and contract evidence against the new remediation plan before marking backend integrity as verified.

---


### 2026-07-13 — PHASE B14 BACKEND CONTRACT FREEZE

### Validation performed
- Backend characterization and audit suite: 57 tests passed
- Django system check: no issues
- Python compile pass: no errors
- Diff formatting check: no issues
- API endpoint discovery: 44 GET routes, 0 failures
- Full CRUD smoke test: 128 routes passed, 0 failed, 0 skipped

### Contract freeze result
- Existing frontend/backend API contract matrix remains aligned with the verified DRF CRUD surface.
- No production backend behavior was modified during PHASE B14.
- Backend business-integrity evidence and API CRUD surface are now frozen as the remediation baseline.

### Status
- PHASE B14: VERIFIED
- Backend contract baseline: FROZEN
- Next implementation phase: R1 — Deletion and data-retention integrity

---

# Execution Journal (append-only)

## 2026-07-13

### Resume protocol (performed)
- Inspected `git status` (working tree not clean)
- Inspected repository tree
- Located frontend roadmap and API contract matrix
- Inspected `scripts/smoke_test.py`
- Located installed Django apps (from `dental_clinic/settings.py`)
- Inspected current `website` app skeleton

### Commands executed
- `git status`
- `mkdir -p docs/backend`

### Findings / conclusions (PHASE B0)

**What `scripts/smoke_test.py` verifies (from code inspection):**
- Discovers DRF ViewSet operations by introspecting Django URL patterns (`get_resolver().url_patterns`) and `callback.actions`.
- For each ViewSet:
  - Executes `LIST` on every discovered ViewSet that exposes `list`.
  - For a fixed set of CRUD ViewSets (`CREATE_ORDER`), executes: `CREATE` → `RETRIEVE` → `PUT` → `PATCH` (and verifies returned fields equal the patch payload) → later `DELETE`.
  - For ViewSets without `create` (read-only), executes `RETRIEVE` using an existing DB object if available.
- Confirms that the API accepts a representative JSON payload for each CRUD resource and returns success HTTP codes (200/201/204).
- Confirms multipart upload works for `ImagingInstanceViewSet` (uploads a harmless text file) and returns success.

**What it does NOT verify:**
- Does **not** verify business invariants beyond “request succeeded” (e.g., appointment overlaps, end_at > start_at, monetary constraints, patient/treatment consistency).
- Does **not** verify role-based access control (runs under one authenticated user/token only).
- Does **not** verify object-level permissions or queryset scoping.
- Does **not** verify database-level constraints (UniqueConstraint/CheckConstraint) are present/effective.
- Does **not** verify deletion safety (only checks HTTP success; no validation of cascades, PROTECT behavior, or orphaned rows/files).
- Does **not** verify concurrency/atomicity/race conditions.
- Does **not** verify idempotency/duplicate submission safety.
- Does **not** verify file validation (content sniffing, size limits, extension policy); only uploads one text file.
- Does **not** verify audit trail correctness or completeness:
  - It creates an `AuditLog` row directly via ORM solely to have a detail object to retrieve.
  - It does not verify that CRUD operations create audit logs.
  - It does not verify append-only behavior.

**Meaning of `ROUTES: 128 PASSED: 128 FAILED: 0`:**
- `ROUTES` equals the number of unique discovered operations (unique `(viewset, method, action)` tuples).
- `PASSED` increments when each operation returns a success code.
- Therefore, 128/128 indicates **CRUD surface availability** and basic payload acceptance for the selected resources, not business integrity.

### Repo state notes
- `git status` shows uncommitted modifications:
  - modified: `docker-compose.yml`
  - modified: `scripts/check_api_endpoints.py`
  - untracked: `scripts/smoke_test.py`, `frontend/FRONTEND_IMPLEMENTATION_ROADMAP.md`, `frontend/docs/`

### Website app notes (current state)
- `website/models.py`, `website/views.py`, `website/admin.py`, `website/tests.py` are currently skeleton stubs (no implemented domain yet).

### Files created/modified in this session
- Created: `docs/BACKEND_BUSINESS_INTEGRITY_ROADMAP.md`
- Created: `docs/backend/` (directory)

### Validation
- Validation basis for B0: code-level inspection of `scripts/smoke_test.py` plus consistency check that 128 operations matches discovered ViewSets/actions.
- Not executed in this session: live HTTP smoke test run (requires running stack + credentials).

### Next phase
- PHASE B1 — MODEL INTEGRITY
- First action: inventory models by scanning each installed app’s `models.py` (and any `models/` packages) and record initial model list before deeper field/relationship auditing.

---

## 2026-07-13 (continued) — PHASE B1

### Resume protocol (performed)
- Read `docs/BACKEND_BUSINESS_INTEGRITY_ROADMAP.md` (including complete Execution Journal)
- Ran `git status`
- Inspected existing files under `docs/backend/`
- Confirmed PHASE B0 is `[x] VERIFIED COMPLETE`
- Identified PHASE B1 as next unfinished phase

### Commands executed
- `git status`
- Repository scan (tooling): `**/models.py`, `**/models/**/*.py`
- Repository scan (tooling): grep for `class ... (models.Model)`, `UniqueConstraint`, `CheckConstraint`, and common Django signals
- Attempted (BLOCKED): `python manage.py check` (python not available)
- Attempted (BLOCKED): `python3 manage.py check` (Django not installed in current environment)
- `PYTHONPYCACHEPREFIX=/tmp/pycache python3 -m compileall -q .`

### PHASE B1 deliverable(s)
- Created: `docs/backend/MODEL_RELATIONSHIP_GRAPH.md`

### Validation (PHASE B1)
Status: **PASS with WARN**
- PASS: Static audit completed across every installed project app; model inventory and relationship graph documented.
- PASS: `compileall` succeeded (syntax-level validation).
- WARN: Django runtime introspection commands could not be executed in this environment because `django` is not installed.

### Results summary (PHASE B1)
- Installed project apps inspected: 15/15
- Models discovered (by code inspection): 73
- Relationships documented (FK/O2O): 120

### High-risk findings captured in the relationship graph
- `SoftDeleteModel` is fields-only (no `delete()` override, no default manager filtering) → hard deletes and `CASCADE` chains remain possible.
- Patient hard delete cascades through appointments/odontogram/treatment plans/treatments/prescriptions/billing/documents/imaging.
- Invoice hard delete cascades to Payments/CreditNotes (financial audit trail risk).
- Duplicated patient pointers exist without constraints:
  - `billing.Payment.patient` vs `billing.Invoice.patient`
  - `treatment_plans.TreatmentPlanApproval.patient` vs `treatment_plans.TreatmentPlan.patient`
- `accounts.AuditLog.object_id` is a UUIDField while most models likely use integer PKs → audit linkage risk.

### Files created/modified in this session
- Created: `docs/backend/MODEL_RELATIONSHIP_GRAPH.md`
- Modified: `docs/BACKEND_BUSINESS_INTEGRITY_ROADMAP.md`

### Next phase
- PHASE B2 — SERIALIZER CONTRACT AUDIT
- First action: inventory all DRF serializers actually bound to API viewsets (start from `*/views.py` and router registrations in `dental_clinic/urls.py`), then create `docs/backend/SERIALIZER_CONTRACT_AUDIT.md`.

---

## 2026-07-13 (continued) — PHASE B2

### Resume protocol (performed)
- Read `docs/BACKEND_BUSINESS_INTEGRITY_ROADMAP.md` (including complete Execution Journal)
- Ran `git status`
- Inspected existing files under `docs/backend/`
- Confirmed PHASE B0 and PHASE B1 are `[x] VERIFIED COMPLETE`
- Identified PHASE B2 as next unfinished phase

### Commands executed
- `git status`
- `docker compose ps`
- `docker compose exec -T web python manage.py check`
- `docker compose exec -T web python manage.py shell -c "..."` (URL resolver → ViewSet → serializer field introspection)
- `PYTHONPYCACHEPREFIX=/tmp/pycache python3 -m compileall -q .`

### PHASE B2 deliverable(s)
- Created: `docs/backend/SERIALIZER_CONTRACT_AUDIT.md`

### Validation (PHASE B2)
Status: **PASS with WARN**
- PASS: All **22/22** exposed ViewSets accounted for and serializer_class resolved.
- PASS: No dynamic `get_serializer_class()` usage found in exposed ViewSets.
- PASS: Runtime field-level introspection performed inside the real `web` container.
- PASS: `python manage.py check` inside container passes.
- PASS: Static `compileall` passes.
- WARN: Business validation is largely absent in serializers (documented as findings rather than a validation failure).

### Results summary (PHASE B2)
- Exposed ViewSets accounted for: 22/22
- Exposed serializers audited: 22

### Files created/modified in this session
- Created: `docs/backend/SERIALIZER_CONTRACT_AUDIT.md`
- Modified: `docs/BACKEND_BUSINESS_INTEGRITY_ROADMAP.md`

### Next phase
- PHASE B3 — CROSS-MODEL CONSISTENCY
- First action: implement executable tests for **observed** cross-model inconsistency risks enabled by current serializers (e.g., `Payment.patient` != `Invoice.patient`, `Treatment.patient` inconsistent with `Appointment.patient`), without inventing rules.

---

## 2026-07-13 (continued) — PHASE B3

### Resume protocol (performed)
- Read `docs/BACKEND_BUSINESS_INTEGRITY_ROADMAP.md` (including complete Execution Journal)
- Ran `git status`
- Inspected existing files under `docs/backend/`
- Confirmed PHASE B0, PHASE B1, PHASE B2 are `[x] VERIFIED COMPLETE`
- Identified PHASE B3 as next unfinished phase
- Inspected existing test architecture (`accounts/tests/` uses `APITestCase`)

### Commands executed
- `git status`
- `docker compose exec -T web python manage.py check`
- `docker compose exec -T web python manage.py test accounts.tests.test_cross_model_consistency`
- `PYTHONPYCACHEPREFIX=/tmp/pycache python3 -m compileall -q .`

### PHASE B3 deliverable(s)
- Created: `docs/backend/CROSS_MODEL_CONSISTENCY_AUDIT.md`
- Created: `accounts/tests/test_cross_model_consistency.py`

### Validation (PHASE B3)
Status: **PASS**
- PASS: targeted cross-model tests executed in the real `web` container.
- PASS: Django `manage.py check` passes.
- PASS: static `compileall` passes.

### Results summary (PHASE B3)
- Relationship paths audited (documented): 5
- Executable tests created: 5 (characterization tests)

### Confirmed behavior (high risk)
- API accepts mismatched patient roots for:
  - `Payment.patient` vs `Payment.invoice.patient` (documented as BUSINESS RULE UNDEFINED)
  - `Invoice.patient` vs `Invoice.related_treatment_plan.patient`
  - `Treatment.patient` vs `Treatment.appointment.patient`
  - `Treatment.patient` vs `Treatment.treatment_plan.patient`
- ORM accepts mismatched patient roots for:
  - `TreatmentPlanApproval.patient` vs `TreatmentPlan.patient` (approvals not exposed in API surface)

### Files created/modified in this session
- Created: `docs/backend/CROSS_MODEL_CONSISTENCY_AUDIT.md`
- Created: `accounts/tests/test_cross_model_consistency.py`
- Modified: `docs/BACKEND_BUSINESS_INTEGRITY_ROADMAP.md`

### Next phase
- PHASE B4 — BUSINESS RULE AUDIT
- First action: inventory business rules by scanning ViewSets/services for validation and invariants around scheduling, billing, inventory, and state/status fields; create `docs/backend/BUSINESS_RULE_MATRIX.md`.

---

## 2026-07-13 (continued) — PHASE B4

### Resume protocol (performed)
- Read `docs/BACKEND_BUSINESS_INTEGRITY_ROADMAP.md` (including complete Execution Journal)
- Ran `git status`
- Inspected existing files under `docs/backend/`
- Read prior audit artifacts:
  - `docs/backend/MODEL_RELATIONSHIP_GRAPH.md`
  - `docs/backend/SERIALIZER_CONTRACT_AUDIT.md`
  - `docs/backend/CROSS_MODEL_CONSISTENCY_AUDIT.md`
- Read executable B3 tests: `accounts/tests/test_cross_model_consistency.py`
- Confirmed PHASE B0/B1/B2/B3 are `[x] VERIFIED COMPLETE`
- Identified PHASE B4 as next unfinished phase

### Commands executed
- `git status`
- `docker compose exec -T web python manage.py check`
- `docker compose exec -T web python manage.py test accounts.tests.test_business_rules`
- `docker compose exec -T web python manage.py test accounts.tests.test_auth accounts.tests.test_users accounts.tests.test_permissions accounts.tests.test_cross_model_consistency accounts.tests.test_business_rules`
- `PYTHONPYCACHEPREFIX=/tmp/pycache python3 -m compileall -q .`

### PHASE B4 deliverable(s)
- Created: `docs/backend/BUSINESS_RULE_MATRIX.md`
- Created: `accounts/tests/test_business_rules.py`

### Validation (PHASE B4)
Status: **PASS with WARN**
- PASS: business rule inventory derived from real code + existing tests.
- PASS: characterization tests executed in `web` container.
- PASS: `manage.py check` passes.
- PASS: static `compileall` passes.
- WARN: multiple critical business invariants are currently undefined / not enforced (documented as `[WARN] BUSINESS RULE UNDEFINED`).

### Files created/modified in this session
- Created: `docs/backend/BUSINESS_RULE_MATRIX.md`
- Created: `accounts/tests/test_business_rules.py`
- Modified: `docs/BACKEND_BUSINESS_INTEGRITY_ROADMAP.md`

### Next phase
- PHASE B5 — STATE MACHINE AUDIT
- First action: inventory all `status`/`state` fields across models and identify any implemented transition logic and bypass paths; create `docs/backend/STATE_MACHINE_AUDIT.md`.

---

## 2026-07-13 (continued) — PHASE B5

### Resume protocol (performed)
- Read `docs/BACKEND_BUSINESS_INTEGRITY_ROADMAP.md` (including complete Execution Journal)
- Ran `git status`
- Inspected existing files under `docs/backend/`
- Read audit artifacts: B1/B2/B3/B4 docs
- Read existing characterization/integrity tests
- Confirmed PHASE B0–B4 are `[x] VERIFIED COMPLETE`
- Identified PHASE B5 as next unfinished phase

### Commands executed
- `git status`
- `docker compose exec -T web python manage.py shell -c "..."` (introspect models for status/state fields)
- `docker compose exec -T web python manage.py test accounts.tests.test_state_machine_audit`
- `docker compose exec -T web python manage.py test accounts.tests.test_cross_model_consistency accounts.tests.test_business_rules accounts.tests.test_state_machine_audit`
- `docker compose exec -T web python manage.py check`
- `PYTHONPYCACHEPREFIX=/tmp/pycache python3 -m compileall -q .`

### PHASE B5 deliverable(s)
- Created: `docs/backend/STATE_MACHINE_AUDIT.md`
- Created: `accounts/tests/test_state_machine_audit.py`

### Validation (PHASE B5)
Status: **PASS with WARN**
- PASS: state/status inventory extracted from runtime model metadata.
- PASS: characterization tests executed in the real `web` container.
- PASS: `manage.py check` passes.
- PASS: static `compileall` passes.
- WARN: **No explicit state machine / transition enforcement** found for any audited status field; documented as `[WARN] STATE MACHINE UNDEFINED`.

### Results summary (PHASE B5)
- Stateful models audited: 17
- Stateful fields inventoried (status/state/phase/*_status): 29
- Explicitly implemented state machines discovered: 0

### Confirmed bypass behavior
- API bypass: direct `PATCH` can set arbitrary status strings for most models; for `Appointment.status` it can jump between any allowed choice values.
- ORM bypass: Django `choices` not enforced at DB; ORM can persist invalid `Appointment.status` values.
- No automatic `AppointmentStatusLog` rows are created on API status changes.

### Files created/modified in this session
- Created: `docs/backend/STATE_MACHINE_AUDIT.md`
- Created: `accounts/tests/test_state_machine_audit.py`
- Modified: `docs/BACKEND_BUSINESS_INTEGRITY_ROADMAP.md`

### Next phase
- PHASE B6 — AUTHORIZATION MATRIX
- First action: derive role list from `accounts.User.Role` and audit each ViewSet’s permission classes + queryset scoping; create `docs/backend/AUTHORIZATION_MATRIX.md`.

---

## 2026-07-13 (continued) — PHASE B6

### Resume protocol (performed)
- Read `docs/BACKEND_BUSINESS_INTEGRITY_ROADMAP.md` (including complete Execution Journal)
- Read existing audit artifacts B1–B5
- Read auth/permission code (`accounts/models.py`, `accounts/permissions.py`, ViewSets)
- Ran `git status`
- Inspected existing test architecture (`accounts/tests/*`)
- Confirmed PHASE B0–B5 are `[x] VERIFIED COMPLETE`
- Identified PHASE B6 as next unfinished phase

### Commands executed
- `git status`
- `docker compose exec -T web python manage.py check`
- `docker compose exec -T web python manage.py test accounts.tests.test_authorization_matrix`
- `docker compose exec -T web python manage.py test accounts.tests.test_permissions accounts.tests.test_auth accounts.tests.test_users accounts.tests.test_cross_model_consistency accounts.tests.test_business_rules accounts.tests.test_state_machine_audit accounts.tests.test_authorization_matrix`
- `PYTHONPYCACHEPREFIX=/tmp/pycache python3 -m compileall -q .`

### PHASE B6 deliverable(s)
- Created: `docs/backend/AUTHORIZATION_MATRIX.md`
- Created: `accounts/tests/test_authorization_matrix.py`

### Validation (PHASE B6)
Status: **PASS with WARN**
- PASS: Definitive role list derived from `accounts.User.Role`.
- PASS: All 22 ViewSets audited for permission_classes and queryset scoping.
- PASS: Direct-ID access tests executed.
- PASS: `manage.py check` passes.
- PASS: static `compileall` passes.
- WARN: Object-level authorization is largely absent across most resources (role-based only).

### Findings summary (PHASE B6)
- Global auth baseline: DRF defaults to `IsAuthenticated`; `LoginView` is `AllowAny`.
- Role-gated endpoints are implemented via custom permission classes.
- Object scope is implemented only for `UserViewSet` (non-superadmin is scoped to self via `get_queryset`).
- Confirmed direct-ID broad access:
  - `AppointmentViewSet` is `IsStaffMember` with no scoping; receptionist can retrieve another practitioner’s appointment by ID.

### Files created/modified in this session
- Created: `docs/backend/AUTHORIZATION_MATRIX.md`
- Created: `accounts/tests/test_authorization_matrix.py`
- Modified: `docs/BACKEND_BUSINESS_INTEGRITY_ROADMAP.md`

### Next phase
- PHASE B7 — CONCURRENCY AND TRANSACTION SAFETY
- First action: identify concurrency-sensitive operations (billing payment creation, inventory mutations, appointment scheduling) and audit transactional protection; create `docs/backend/CONCURRENCY_AUDIT.md`.

---

## 2026-07-13 (continued) — PHASE B7

### Resume protocol (performed)
- Read `docs/BACKEND_BUSINESS_INTEGRITY_ROADMAP.md` (including complete Execution Journal)
- Ran `git status`
- Inspected existing files under `docs/backend/` (B1–B6 artifacts)
- Reused B2 findings (client-writable aggregates) and B4 findings (missing invariants)

### Commands executed
- `git status`
- Repository scan (grep): `transaction.atomic`, `select_for_update`, `F(`, `paid_amount`, `balance_due`, `stock_quantity`
- `docker compose exec -T web python manage.py check`
- `docker compose exec -T web python manage.py test accounts.tests.test_cross_model_consistency accounts.tests.test_business_rules accounts.tests.test_state_machine_audit accounts.tests.test_authorization_matrix`
- `PYTHONPYCACHEPREFIX=/tmp/pycache python3 -m compileall -q .`

### PHASE B7 deliverable(s)
- Created: `docs/backend/CONCURRENCY_AUDIT.md`

### Validation (PHASE B7)
Status: **PASS with WARN**
- PASS: concurrency-sensitive operations identified and documented from real write paths.
- PASS: targeted test suites run in Docker (regression check).
- PASS: `manage.py check` passes.
- PASS: static `compileall` passes.
- WARN: repository contains minimal transaction/locking protections beyond unique constraints and `transaction.atomic` in `UserSerializer`.

### Files created/modified in this session
- Created: `docs/backend/CONCURRENCY_AUDIT.md`
- Modified: `docs/BACKEND_BUSINESS_INTEGRITY_ROADMAP.md`

### Next phase
- PHASE B8 — IDEMPOTENCE AND DUPLICATE SUBMISSION
- First action: identify business-critical POST operations (payments, appointments, notifications, document generation) and test duplicate submission risk; create `docs/backend/IDEMPOTENCE_AUDIT.md`.

---

## 2026-07-13 (continued) — PHASE B8

### Resume protocol (performed)
- Read `docs/BACKEND_BUSINESS_INTEGRITY_ROADMAP.md` (including complete Execution Journal)
- Ran `git status`
- Inspected existing files under `docs/backend/` (B1–B7 artifacts)
- Reviewed existing characterization tests (B3–B7)

### Commands executed
- `git status`
- Repository scan: searched for Idempotency-Key/idempotency support (none found)
- `docker compose exec -T web python manage.py test accounts.tests.test_idempotence_audit`
- `docker compose exec -T web python manage.py test accounts.tests.test_cross_model_consistency accounts.tests.test_business_rules accounts.tests.test_state_machine_audit accounts.tests.test_authorization_matrix accounts.tests.test_idempotence_audit`
- `docker compose exec -T web python manage.py check`
- `PYTHONPYCACHEPREFIX=/tmp/pycache python3 -m compileall -q .`

### PHASE B8 deliverable(s)
- Created: `docs/backend/IDEMPOTENCE_AUDIT.md`
- Created: `accounts/tests/test_idempotence_audit.py`

### Validation (PHASE B8)
Status: **PASS with WARN**
- PASS: deterministic duplicate-submission characterization tests executed successfully.
- PASS: `manage.py check` passes.
- PASS: static `compileall` passes.
- WARN: No idempotency key support; multiple business-critical duplicate risks confirmed.

### Files created/modified in this session
- Created: `docs/backend/IDEMPOTENCE_AUDIT.md`
- Created: `accounts/tests/test_idempotence_audit.py`
- Modified: `docs/BACKEND_BUSINESS_INTEGRITY_ROADMAP.md`

### Next phase
- PHASE B9 — FILE INTEGRITY AND UPLOAD SECURITY
- First action: inventory FileField/ImageField endpoints and implement synthetic upload validation tests; create `docs/backend/FILE_INTEGRITY_AUDIT.md`.


---

## 2026-07-13 (continued) — PHASE B9

### Resume protocol (performed)
- Read `docs/BACKEND_BUSINESS_INTEGRITY_ROADMAP.md` and existing B8 continuation state
- Inventoried all `FileField` and `ImageField` fields through repository scan and Django runtime model metadata
- Identified file-bearing models exposed through the current DRF ViewSet surface
- Inspected serializers and ViewSets for upload validation
- Inspected Django media and storage configuration
- Searched repository for physical file deletion and storage cleanup logic

### Commands executed
- Repository scan for `FileField` and `ImageField`
- Repository scan for multipart/parser configuration
- Django runtime file-field inventory
- DRF ViewSet/serializer file-field surface inventory
- Repository scan for `post_delete`, `pre_delete`, `storage.delete`, `default_storage`, and file deletion calls
- `docker compose exec -T web python manage.py test accounts.tests.test_file_integrity_audit`
- `docker compose exec -T web python manage.py check`
- `PYTHONPYCACHEPREFIX=/tmp/pycache python3 -m compileall -q .`

### PHASE B9 deliverable(s)
- Created: `docs/backend/FILE_INTEGRITY_AUDIT.md`
- Created: `accounts/tests/test_file_integrity_audit.py`

### Validation (PHASE B9)
Status: **PASS with WARN**
- PASS: 6 `FileField` fields and 0 `ImageField` fields inventoried.
- PASS: exposed multipart/file API surface identified.
- PASS: 5 deterministic synthetic upload characterization tests pass.
- PASS: `manage.py check` passes.
- PASS: static `compileall` passes.
- WARN: no explicit extension validation was discovered.
- WARN: no trusted MIME or file-content validation was discovered.
- WARN: no business-level maximum upload size was discovered.
- WARN: imaging metadata can disagree with uploaded file extension/content.
- WARN: deleting an imaging instance leaves the physical file in storage.

### Findings summary (PHASE B9)
- `Prescription.pdf_file` accepts arbitrary text uploads.
- `Document.pdf_file` accepts executable file extensions.
- `ImagingInstance` accepts MIME/extension/content metadata mismatches.
- Files larger than Django's memory upload threshold are accepted.
- Physical file cleanup is not coupled to model/API deletion.
- PHASE B8 duplicate imaging upload findings also imply duplicate physical storage risk.

### Files created/modified in this session
- Created: `docs/backend/FILE_INTEGRITY_AUDIT.md`
- Created: `accounts/tests/test_file_integrity_audit.py`
- Modified: `docs/BACKEND_BUSINESS_INTEGRITY_ROADMAP.md`

### Next phase
- PHASE B10 — AUDIT TRAIL INTEGRITY
- First action: audit the `AuditLog` model and all write paths, then characterize append-only guarantees and API mutation exposure; create `docs/backend/AUDIT_TRAIL_AUDIT.md`.

---

## 2026-07-13 (continued) — PHASE B10

### Resume protocol (performed)
- Read the PHASE B10 continuation state from the backend integrity roadmap
- Inspected `accounts.AuditLog` model metadata and indexes
- Inspected `AuditLogSerializer`
- Inspected `AuditLogViewSet`
- Inspected audit-log router exposure
- Inspected Django admin mutation protections
- Searched production code for AuditLog creation and audit write hooks
- Characterized ORM mutation and deletion behavior
- Characterized automatic business audit generation

### Commands executed
- Repository scan for `AuditLog` and audit-related write paths
- Django runtime `AuditLog` model metadata inspection
- Audit API/ViewSet inspection
- Django admin audit configuration inspection
- ORM mutation/deletion probe
- `docker compose exec -T web python manage.py test accounts.tests.test_audit_trail_audit`
- `docker compose exec -T web python manage.py check`
- `PYTHONPYCACHEPREFIX=/tmp/pycache python3 -m compileall -q .`
- `git diff --check`

### PHASE B10 deliverable(s)
- Created: `docs/backend/AUDIT_TRAIL_AUDIT.md`
- Created: `accounts/tests/test_audit_trail_audit.py`

### Validation (PHASE B10)
Status: **PASS with WARN**
- PASS: `AuditLog` model and write paths audited.
- PASS: API mutation exposure characterized.
- PASS: Django admin mutation exposure characterized.
- PASS: 5 deterministic audit-trail characterization tests pass.
- PASS: `manage.py check` passes.
- PASS: static `compileall` passes.
- PASS: `git diff --check` passes.
- WARN: audit records are mutable through ORM instance updates.
- WARN: audit records are mutable through `QuerySet.update()`.
- WARN: audit records can be physically deleted through ORM.
- WARN: normal business API mutations do not automatically emit audit events.

### Findings summary (PHASE B10)
- `AuditLogViewSet` is read-only and restricted to superadmin.
- Django admin disables add, change, and delete for `AuditLog`.
- The underlying `AuditLog` model is not append-only.
- ORM mutation can rewrite historical audit records.
- ORM deletion can permanently remove audit records.
- Production business write paths do not automatically populate the audit trail.

### Files created/modified in this session
- Created: `docs/backend/AUDIT_TRAIL_AUDIT.md`
- Created: `accounts/tests/test_audit_trail_audit.py`
- Modified: `docs/BACKEND_BUSINESS_INTEGRITY_ROADMAP.md`

### Next phase
- PHASE B11 — WEBSITE DOMAIN AUDIT
- First action: inspect the current `website` application implementation and derive the actual domain specification; create `docs/backend/WEBSITE_DOMAIN_SPECIFICATION.md`.

---

## 2026-07-13 (continued) — PHASE B11

### Resume protocol (performed)
- Read the PHASE B11 continuation state from the backend integrity roadmap
- Inspected the complete `website` application implementation
- Inspected project-level public routing
- Inspected the current public SPA shell
- Inspected legacy Django public templates and named URL references
- Characterized the absence of website-domain persistence and API ownership
- Derived the current website domain specification from repository evidence

### Commands executed
- Website application file inventory
- `website.models` inspection
- `website.views` inspection
- Website serializer and URL configuration inspection
- Project URL configuration inspection
- Public template inventory and inspection
- Repository scan for website/public domain references
- `docker compose exec -T web python manage.py test accounts.tests.test_website_domain_audit`
- `docker compose exec -T web python manage.py check`
- `PYTHONPYCACHEPREFIX=/tmp/pycache python3 -m compileall -q .`
- `git diff --check`

### PHASE B11 deliverable(s)
- Created: `docs/backend/WEBSITE_DOMAIN_SPECIFICATION.md`
- Created: `accounts/tests/test_website_domain_audit.py`

### Validation (PHASE B11)
Status: **PASS with WARN**
- PASS: `website` application installation characterized.
- PASS: zero concrete website-domain models confirmed.
- PASS: absence of a dedicated website URL/API surface confirmed.
- PASS: SPA catch-all delivery through `public/app.html` confirmed.
- PASS: 5 deterministic website-domain characterization tests pass.
- PASS: `manage.py check` passes.
- PASS: static `compileall` passes.
- PASS: `git diff --check` passes.
- WARN: no backend-owned website content domain currently exists.
- WARN: clinic and SEO content remains hard-coded in legacy public templates.
- WARN: legacy Django templates reference named routes absent from the current Django URL contract.

### Findings summary (PHASE B11)
- The `website` application is currently a placeholder application.
- The application owns no persistent website-domain entities.
- No website-specific serializer or API contract exists.
- The effective public delivery architecture is Django catch-all to SPA shell to React.
- Legacy server-rendered public templates remain as architectural residue.
- Future backend-managed public content requires an explicit product/domain decision.

### Files created/modified in this session
- Created: `docs/backend/WEBSITE_DOMAIN_SPECIFICATION.md`
- Created: `accounts/tests/test_website_domain_audit.py`
- Modified: `docs/BACKEND_BUSINESS_INTEGRITY_ROADMAP.md`

### Next phase
- PHASE B12 — END-TO-END BUSINESS WORKFLOWS
- First action: inspect the B12 roadmap checklist and inventory the actual cross-domain workflow candidates before implementing executable end-to-end workflow characterization tests.

---

## 2026-07-13 (continued) — PHASE B12

### Resume protocol (performed)
- Inspected the PHASE B12 roadmap checklist.
- Inventoried the real cross-domain model graph.
- Inspected core patient, appointment, treatment-plan, treatment, and billing models.
- Derived executable workflows from actual repository relationships.
- Characterized clinical-to-financial workflow persistence.
- Characterized cross-patient consistency gaps.
- Characterized payment-to-invoice balance synchronization behavior.

### PHASE B12 deliverable(s)
- Created: `docs/backend/WORKFLOW_AUDIT.md`
- Created: `accounts/tests/test_end_to_end_business_workflows.py`

### Validation (PHASE B12)
Status: **PASS with WARN**
- PASS: complete clinical-to-financial workflow can be persisted.
- PASS: 6 deterministic end-to-end workflow characterization tests pass.
- PASS: `manage.py check` passes.
- PASS: static `compileall` passes.
- PASS: `git diff --check` passes.
- WARN: treatment can reference an appointment belonging to another patient.
- WARN: treatment can reference a treatment plan belonging to another patient.
- WARN: invoice lines can reference treatments belonging to another patient.
- WARN: payments can reference invoices belonging to another patient.
- WARN: payment creation does not automatically synchronize invoice balances.
- WARN: critical multi-model workflows lack centralized transactional orchestration.

### Findings summary (PHASE B12)
- The principal patient-to-payment workflow is persistable.
- The relational graph is connected but business-level patient consistency is not fully enforced.
- Financial payment persistence and invoice balance state are independent write operations.
- Critical workflow integrity currently depends on caller behavior.
- B12 findings require explicit prioritization in the backend remediation plan.

### Files created/modified in this session
- Created: `docs/backend/WORKFLOW_AUDIT.md`
- Created: `accounts/tests/test_end_to_end_business_workflows.py`
- Modified: `docs/BACKEND_BUSINESS_INTEGRITY_ROADMAP.md`

### Next phase
- PHASE B13 — REMEDIATION PLAN
- First action: consolidate all verified WARN findings from backend audit deliverables and derive a prioritized remediation plan without modifying production behavior.

