# Domain Coherence Tracker — G1 to G13

## Purpose

This document is the source of truth for the domain coherence review.

The review validates the business architecture of the dental clinic application before remediation.

No model, serializer, view, migration, or API contract is modified during the G1-G13 review.

## Status Legend

- `TODO` — domain not reviewed
- `IN_PROGRESS` — domain review active
- `DONE` — domain logic, relations, invariants, and technical impacts reviewed and validated

## Review Method

For every domain group:

1. Define the real business domain.
2. Map involved models.
3. Verify database relations.
4. Verify business relations.
5. Identify missing relations.
6. Identify duplicated sources of truth.
7. Define business invariants.
8. Audit serializers against those invariants.
9. Evaluate view and permission impact.
10. Evaluate API and frontend impact.
11. Evaluate migration risk.
12. Compare findings with PHASE B0-B12 audits.
13. Record the final domain verdict.

---

# Domain Groups

| Group | Domain | Status |
|---|---|---|
| G1 | Internal Identity, Staff & Website Administration | IN_PROGRESS |
| G2 | Patient Core | TODO |
| G3 | Scheduling | TODO |
| G4 | Odontogram | TODO |
| G5 | Treatment Planning | TODO |
| G6 | Clinical Treatment | TODO |
| G7 | Billing | TODO |
| G8 | Inventory | TODO |
| G9 | Prescriptions | TODO |
| G10 | Imaging | TODO |
| G11 | Document Management | TODO |
| G12 | Notifications & Workflow | TODO |
| G13 | Reporting & Global Read Domain | TODO |

---

# G1 — Internal Identity, Staff & Website Administration

Status: `IN_PROGRESS`

## Domain Definition

`accounts.User` represents only authenticated internal application users.

Current internal roles:

- SUPER_ADMIN
- ADMINISTRATOR
- DENTIST
- ASSISTANT
- RECEPTIONIST
- ACCOUNTANT

A patient is not an `accounts.User`.

A public website visitor is not an `accounts.User`.

## Domain Graph

```text
                         accounts.User
                               |
               +---------------+---------------+
               |                               |
               v                               v
       staff.StaffProfile                   website
               |                               |
       professional / HR              public website
       identity                       administration
                                               ^
                                               |
                                          SUPER_ADMIN
