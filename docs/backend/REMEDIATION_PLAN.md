# BACKEND BUSINESS INTEGRITY REMEDIATION PLAN

## Status

PHASE B13 consolidates verified backend audit findings and prioritizes remediation work for the existing Django/DRF backend.

This phase does not claim that any risk has already been fixed. It documents verified gaps, risks, and the recommended implementation order for future remediation work.

## Scope

This remediation plan is derived from the following verified audit deliverables:

- [docs/backend/MODEL_RELATIONSHIP_GRAPH.md](MODEL_RELATIONSHIP_GRAPH.md)
- [docs/backend/SERIALIZER_CONTRACT_AUDIT.md](SERIALIZER_CONTRACT_AUDIT.md)
- [docs/backend/CROSS_MODEL_CONSISTENCY_AUDIT.md](CROSS_MODEL_CONSISTENCY_AUDIT.md)
- [docs/backend/BUSINESS_RULE_MATRIX.md](BUSINESS_RULE_MATRIX.md)
- [docs/backend/STATE_MACHINE_AUDIT.md](STATE_MACHINE_AUDIT.md)
- [docs/backend/CONCURRENCY_AUDIT.md](CONCURRENCY_AUDIT.md)
- [docs/backend/AUTHORIZATION_MATRIX.md](AUTHORIZATION_MATRIX.md)
- [docs/backend/IDEMPOTENCE_AUDIT.md](IDEMPOTENCE_AUDIT.md)
- [docs/backend/FILE_INTEGRITY_AUDIT.md](FILE_INTEGRITY_AUDIT.md)
- [docs/backend/AUDIT_TRAIL_AUDIT.md](AUDIT_TRAIL_AUDIT.md)
- [docs/backend/WEBSITE_DOMAIN_SPECIFICATION.md](WEBSITE_DOMAIN_SPECIFICATION.md)
- [docs/backend/WORKFLOW_AUDIT.md](WORKFLOW_AUDIT.md)

## Prioritization Method

Remediation items are prioritized using the following scheme:

- P0 — CRITICAL integrity/security/data-loss risk
- P1 — HIGH integrity or workflow correctness risk
- P2 — MEDIUM architectural or operational risk
- P3 — LOW / deferred / product-decision-dependent risk

Prioritization is derived from:

1. confirmed evidence in the audit documents,
2. practical dependency order for implementing safeguards, and
3. the likelihood that a gap can cause irreversible data loss, financial inconsistency, or uncontrolled state changes.

## Executive Risk Summary

The verified audit evidence points to a small number of coherent backend integrity themes:

- Deletion semantics are incomplete. Soft-delete flags exist, but the repository still allows hard-delete behavior that can cascade through clinical and financial history.
- Financial integrity is weak. Invoice totals and balances are client-writable, payments are not atomically tied to invoice state, and payment/invoice balance invariants are not enforced.
- Cross-model consistency is not enforced. The backend permits mismatched patient ownership across treatments, appointments, treatment plans, invoices, invoice lines, and payments.
- Workflow correctness is not controlled by a shared service boundary. Critical multi-model workflows rely on caller discipline rather than transactionally coordinated services.
- State and lifecycle controls are largely undefined. Many status fields are free text, and direct PATCH operations can change state without transition rules.
- Access control is mostly role-based and does not consistently provide object-level enforcement.
- File handling lacks validation, lifecycle cleanup, and duplicate detection.
- Audit trail coverage and immutability are incomplete.
- Website backend ownership remains undefined and is not yet a formal domain boundary.

## Remediation Dependency Order

The recommended implementation order is as follows:

1. Deletion semantics and retention safety
   - Establish safe delete semantics before other safeguards are layered on top.
   - This reduces the chance of irreversible loss while later integrity controls are implemented.

2. Serializer ownership and write-contract hardening
   - Server-owned fields must be made immutable at the API boundary before relying on service orchestration.
   - This prevents client-side tampering of financial and audit-sensitive data.

3. Cross-model consistency enforcement
   - Patient and ownership consistency rules should be enforced before orchestrating multi-model workflows.
   - This prevents invalid clinical-to-financial records from being created.

4. Transactional workflow services
   - Critical workflows such as payment posting and treatment/appointment/treatment-plan linkage should be coordinated in services with transaction boundaries.
   - This protects later financial and state-machine work from partial updates.

5. Financial invariants and billing integrity
   - Invoice totals, balances, and payment behavior should be made server-controlled and atomic once workflow boundaries exist.

6. State machines and transition enforcement
   - Explicit state definitions and transition rules can then be implemented without bypassing business workflow logic.

7. Authorization scope
   - Once the core object graph is protected, object-level access rules can be layered onto the same workflows.

8. File lifecycle and content validation
   - File behavior is easier to harden once storage and workflow ownership are well defined.

9. Audit trail completeness and immutability
   - Audit capabilities should be added where business changes are meaningful and where tamper resistance is required.

10. Asynchronous and idempotent workflow hardening
   - Duplicate send/claim workflows should be hardened after the primary state and transaction model is defined.

11. Website domain decision and ownership
   - The website domain should be resolved as a product decision once the core backend integrity model is stable.

## Prioritized Remediation Matrix

| ID | Priority | Domain | Verified Finding | Evidence | Recommended Remediation | Dependencies | Validation Strategy |
|---|---|---|---|---|---|---|---|
| REM-P0-001 | P0 | Deletion safety | Hard-delete and cascade chains can remove clinical and financial history. | MODEL_RELATIONSHIP_GRAPH.md; BUSINESS_RULE_MATRIX.md | Replace destructive cascade behavior with safer deletion semantics, review on_delete policies, and define explicit retention/deletion policy before enabling destructive operations. | None | Model-level regression tests, delete-path tests, data retention checks |
| REM-P0-002 | P0 | Billing integrity | Invoice totals and balances are client-writable and not server-calculated. | SERIALIZER_CONTRACT_AUDIT.md; BUSINESS_RULE_MATRIX.md; CONCURRENCY_AUDIT.md; WORKFLOW_AUDIT.md | Make financial aggregates read-only in API contracts and calculate them server-side from underlying transactions. | REM-P0-001 | API contract tests, service tests, negative tests for client tampering |
| REM-P0-003 | P0 | Payment atomicity | Payment persistence does not synchronize invoice balances and lacks invariants for positive amounts and overpayment risk. | BUSINESS_RULE_MATRIX.md; CONCURRENCY_AUDIT.md; WORKFLOW_AUDIT.md | Introduce transactional payment service that updates invoice state atomically and enforces payment amount invariants. | REM-P0-002 | Transaction tests, overpayment tests, concurrency tests |
| REM-P1-001 | P1 | Cross-model consistency | Patient ownership mismatches are accepted across treatments, appointments, treatment plans, invoices, invoice lines, and payments. | CROSS_MODEL_CONSISTENCY_AUDIT.md; WORKFLOW_AUDIT.md; BUSINESS_RULE_MATRIX.md | Define and enforce cross-model ownership/consistency rules in shared validation or service layer. | REM-P0-001 | Cross-model negative tests, workflow tests |
| REM-P1-002 | P1 | Scheduling integrity | Appointment ordering and overlap semantics are not enforced. | BUSINESS_RULE_MATRIX.md; CONCURRENCY_AUDIT.md; STATE_MACHINE_AUDIT.md | Define scheduling rules and enforce them in validation and transactional service boundaries. | REM-P1-001 | Scheduling negative tests, overlapping appointment tests |
| REM-P1-003 | P1 | Inventory integrity | Inventory quantities can be moved into invalid negative states. | BUSINESS_RULE_MATRIX.md; CONCURRENCY_AUDIT.md | Enforce non-negative stock invariants with server-controlled updates and transaction protection. | REM-P0-001 | Inventory service tests, concurrency tests |
| REM-P1-004 | P1 | State machine enforcement | Status fields are mostly free text and direct PATCH can bypass state logic. | STATE_MACHINE_AUDIT.md; BUSINESS_RULE_MATRIX.md; SERIALIZER_CONTRACT_AUDIT.md | Introduce explicit state definitions and transition enforcement for workflow-critical status fields. | REM-P1-002 | State transition tests, negative state-jump tests |
| REM-P1-005 | P1 | Authorization scope | Object-level authorization is largely absent. | AUTHORIZATION_MATRIX.md; BUSINESS_RULE_MATRIX.md | Expand authorization beyond role checks to enforce object-level access patterns for business resources. | REM-P1-001 | Authorization matrix tests, role-scoping tests |
| REM-P1-006 | P1 | Upload validation | File extension, MIME, signature, size, and metadata consistency are not validated. | FILE_INTEGRITY_AUDIT.md; SERIALIZER_CONTRACT_AUDIT.md | Add explicit upload validation and content inspection rules, with domain-specific limits where required. | REM-P1-004 | File integrity tests, negative upload tests |
| REM-P2-001 | P2 | File lifecycle | Physical file cleanup is not implemented and orphan files can remain after deletion. | FILE_INTEGRITY_AUDIT.md | Add file lifecycle handling for delete/update operations and ensure physical storage cleanup is covered. | REM-P0-001 | File deletion behavior tests |
| REM-P2-002 | P2 | Duplicate handling | Duplicate uploads and duplicate create operations are accepted for several workflows. | IDEMPOTENCE_AUDIT.md; FILE_INTEGRITY_AUDIT.md | Add duplicate detection or idempotency handling for workflow-critical create operations. | REM-P1-006 | Idempotency tests and retry tests |
| REM-P2-003 | P2 | Workflow orchestration | Critical multi-model workflows lack transactionally coordinated services. | WORKFLOW_AUDIT.md; CONCURRENCY_AUDIT.md | Introduce service-layer orchestration for multi-model workflows to reduce partial state and caller reliance. | REM-P1-001, REM-P0-003 | Workflow integration tests |
| REM-P2-004 | P2 | Audit completeness | Audit coverage is incomplete and audit records are mutable at the persistence layer. | AUDIT_TRAIL_AUDIT.md | Define audit generation points and strengthen append-only protections for audit data. | REM-P1-004 | Audit trail tests, mutation tests |
| REM-P3-001 | P3 | Website domain ownership | Backend ownership of website content is undefined. | WEBSITE_DOMAIN_SPECIFICATION.md | Resolve domain ownership and public-content management responsibility through explicit product decision. | None | Domain boundary tests and product decision record |
| REM-P3-002 | P3 | Policy-dependent lifecycle controls | Some retention, token, and workflow rules are not defined by current code. | BUSINESS_RULE_MATRIX.md; AUTHORIZATION_MATRIX.md | Capture product/domain decisions before implementing policy-specific retention or token lifecycle controls. | REM-P1-005 | Policy documentation and validation |

## P0 — Critical Remediation

The following verified risks justify P0 treatment:

### 1. Destructive deletion and cascade risk

Evidence from the model relationship graph and business rule matrix shows that soft-delete flags exist, but the repository still allows hard-delete behavior that can cascade through patient, clinical, and financial history. This represents a direct data-loss risk and should be treated as a foundational remediation before other safeguards are added.

### 2. Financial aggregate tampering and billing integrity

The serializer audit and business rule matrix show that invoice totals and balances are exposed as writable fields and are not server-derived. The workflow and concurrency audits confirm that payments do not automatically reconcile invoice balances. Because this affects financial integrity and can create inconsistent ledgers, this deserves critical priority.

### 3. Payment/invoice atomicity and overpayment risk

The business rule matrix, concurrency audit, and workflow audit all indicate that payment creation is not coordinated with invoice state updates and that payment amount invariants are not enforced. This is a confirmed integrity risk for billing workflows and should be handled with transaction-safe service logic.

## P1 — High-Priority Remediation

The following verified findings support P1 treatment:

- Cross-patient relationship consistency across treatments, appointments, treatment plans, invoice lines, and payments.
- Scheduling invariants for appointment ordering and overlap semantics.
- Inventory non-negative constraints.
- Explicit state-machine enforcement for workflow-critical status fields.
- Object-level authorization for business resources.
- Upload validation for file type, content, size, and metadata consistency.

These risks are not merely cosmetic; they affect workflow correctness and can create incorrect or unauthorized business records.

## P2 — Medium-Priority Remediation

The following items are supported by the audits and should be addressed after the core integrity controls:

- file lifecycle cleanup and orphan-file remediation,
- duplicate file and duplicate create handling,
- notification send/claim workflow hardening,
- server-controlled attribution fields,
- audit trail completeness and immutability,
- secondary state-machine gaps beyond the primary workflow states.

## P3 — Deferred / Decision-Dependent Remediation

The following items are recommended only after the core integrity model is stabilized:

- website-domain ownership and public content management responsibility,
- retention-policy decisions,
- token lifecycle or authentication policy decisions,
- low-risk state-field policy definitions that are not yet evidenced by business requirements.

These items should be implemented only after explicit product/domain decisions are captured.

## Proposed Implementation Phases

### R1 — Deletion and data-retention integrity
- Objective: prevent destructive data loss and define safe deletion semantics.
- Primary affected domains: patient, clinical, financial, document, imaging, audit records.
- Prerequisite phases: none.
- Expected test strategy: delete-path regression tests, cascade expectations, retention policy tests.

### R2 — Serializer ownership and write-contract hardening
- Objective: prevent client tampering of server-owned fields and financial aggregates.
- Primary affected domains: billing, documents, audit, user identity fields.
- Prerequisite phases: R1.
- Expected test strategy: API contract tests, negative tests for read-only fields, serialization regression tests.

### R3 — Cross-model consistency
- Objective: enforce patient and ownership consistency across related entities.
- Primary affected domains: appointments, treatments, treatment plans, invoices, payments.
- Prerequisite phases: R2.
- Expected test strategy: cross-model negative tests and workflow-level regression tests.

### R4 — Transactional workflow services
- Objective: centralize multi-model workflow execution in transactional service boundaries.
- Primary affected domains: billing, scheduling, treatment workflows.
- Prerequisite phases: R3.
- Expected test strategy: transaction rollback tests, partial-workflow tests, service integration tests.

### R5 — Billing integrity
- Objective: make payments, balances, and invoice state server-controlled and atomic.
- Primary affected domains: billing.
- Prerequisite phases: R4.
- Expected test strategy: payment/invoice balance tests, overpayment/underpayment tests, concurrency tests.

### R6 — State machines
- Objective: replace free-text status handling with explicit state definitions and transitions.
- Primary affected domains: appointments, treatments, invoices, payments, documents, notifications, imaging.
- Prerequisite phases: R4.
- Expected test strategy: transition tests, invalid-state jump tests, state-log tests.

### R7 — Authorization scope
- Objective: enforce object-level authorization for business resources.
- Primary affected domains: appointments, treatments, invoices, documents, patients, staff.
- Prerequisite phases: R3, R6.
- Expected test strategy: authorization matrix tests, object-level permission tests.

### R8 — File integrity and lifecycle
- Objective: add content validation, size checks, duplicate detection, and storage cleanup.
- Primary affected domains: documents, prescriptions, imaging.
- Prerequisite phases: R2, R4.
- Expected test strategy: upload validation tests, duplicate-file tests, orphan-file cleanup tests.

### R9 — Audit trail completeness
- Objective: make audit generation comprehensive and resistant to tampering.
- Primary affected domains: audit logging, business mutations.
- Prerequisite phases: R6, R7.
- Expected test strategy: audit record creation tests, mutation-blocking tests, append-only assertions.

### R10 — Asynchronous and idempotent workflow hardening
- Objective: reduce duplicate-create and duplicate-send risks in asynchronous workflows.
- Primary affected domains: notifications, imaging, appointments, payments.
- Prerequisite phases: R4, R6, R8.
- Expected test strategy: retry-idempotency tests, concurrent send/claim tests.

## Validation Strategy

Remediation work should be validated through the following mechanisms:

- Preserve the existing characterization tests as regression evidence.
- Add new negative tests for each enforced rule, especially for invalid state transitions, mismatched ownership, tampered financial fields, and duplicate submissions.
- Add API contract tests for read-only and server-controlled fields.
- Add model and service tests for invariants that should be enforced in the backend layer.
- Add transaction tests for multi-step workflows.
- Add concurrency tests where shared-state updates are involved, including payments, stock, appointment scheduling, and notification claim/send paths.
- Add authorization matrix tests to confirm object-level behavior.
- Add file integrity tests for extension, MIME/content, size, duplicate handling, and file cleanup.
- Add audit trail assertions to confirm business mutations are recorded and audit records are protected.
- Run `manage.py check`.
- Run the full Django test suite.
- Run `python3 -m compileall -q .`.
- Run `git diff --check`.

## Explicit Non-Goals

PHASE B13 does not:

- modify production backend behavior,
- implement fixes,
- create migrations,
- define unsupported business policy,
- redesign the frontend,
- introduce infrastructure unrelated to verified findings.

## Final Recommendation

The recommended starting remediation phase is R1 — deletion and data-retention integrity.

This should be first because it addresses the most irreversible risk class in the verified evidence: accidental or destructive loss of clinical and financial history. Establishing safe deletion semantics first also reduces the risk of later remediation work being built on unsafe assumptions.

## R5 — State machine enforcement

Objectif :
Introduire une architecture WorkflowStateMachine centralisée pour tous les workflows métier critiques.

Scope :
- Appointment
- TreatmentPlan
- Treatment
- Invoice
- Payment
- Prescription
- Document
- Notification

Principes :
- interdiction des modifications directes de status,
- transitions explicites uniquement,
- validation centralisée,
- audit des transitions,
- contrôle des permissions,
- opérations atomiques.
