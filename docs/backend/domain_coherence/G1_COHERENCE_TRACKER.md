# G1 — Internal Identity, Staff & Website Administration

Status: `DONE`

## Domain Definition

G1 covers the internal identity, authentication-facing user model, staff professional and HR identity, staff lifecycle, staff hierarchy, contractual information, working schedules, attendance, leave management, staff history, and public website administration boundary.

The verified domain boundary is:

* `accounts.User` represents an authenticated internal application identity.
* `staff.StaffProfile` represents the professional and HR identity of an internal staff member.
* A patient is not an `accounts.User`.
* A public website visitor is not an `accounts.User`.
* Authentication identity and HR identity are separate business concepts.
* The current `website` application does not demonstrate an implemented website administration domain.

Current internal roles are:

* `SUPER_ADMIN`
* `ADMINISTRATOR`
* `DENTIST`
* `ASSISTANT`
* `RECEPTIONIST`
* `ACCOUNTANT`

No patient or public visitor role exists in `accounts.User`.

---

## Models Involved

### accounts.User

Business responsibility:

* internal authentication identity;
* application role;
* account activation state;
* soft deletion state;
* application language;
* application timezone;
* last login IP storage.

Relevant fields:

* `email`
* `first_name`
* `last_name`
* `phone`
* `role`
* `timezone`
* `language`
* `last_login_ip`
* `is_staff`
* `is_active`
* inherited `is_deleted`
* inherited permission fields from `PermissionsMixin`

`email` is the authentication identifier through `USERNAME_FIELD`.

`UserManager` enforces on creation:

* email is required;
* first name is required;
* last name is required;
* role is required;
* role must belong to `User.Role.values`;
* password is required.

`create_superuser()` forces the role to `SUPER_ADMIN` and requires:

* `is_staff=True`;
* `is_superuser=True`.

### accounts.UserLoginHistory

Business responsibility:

* record successful and failed login attempts.

Relations:

* optional `user -> accounts.User`.

Relevant audit data:

* login timestamp;
* source IP;
* user agent;
* success state.

The optional user relation allows failed or unresolved login attempts to remain recorded.

No G1 structural incoherence is demonstrated in the inspected model.

### accounts.AuditLog

Business responsibility:

* store an auditable trace of important application actions.

Relations:

* optional `user -> accounts.User`.

Relevant data:

* action;
* model name;
* UUID object identifier;
* changes;
* context;
* IP address;
* sensitive flag.

The model is generic and is expected to interact with all business domains.

Its global cross-domain responsibility must be reviewed again during the G13 global read/reporting and final coherence scan.

### staff.StaffProfile

Business responsibility:

* professional identity;
* HR identity;
* employee number;
* employment lifecycle;
* department;
* job title;
* employment type;
* management hierarchy;
* working-hours data;
* base salary data;
* staff status;
* HR notes.

Relation:

* mandatory `OneToOne` relation to `accounts.User`.

Additional relation:

* optional self-referencing `manager -> staff.StaffProfile`.

### staff.Contract

Business responsibility:

* staff contractual information.

Relation:

* mandatory `staff -> StaffProfile`.

Relevant data:

* contract type;
* start date;
* end date;
* salary;
* working time;
* status.

### staff.WorkSchedule

Business responsibility:

* structured staff working schedule.

Relation:

* mandatory `staff -> StaffProfile`.

Relevant data:

* weekday;
* start time;
* end time;
* active state.

### staff.AttendanceRecord

Business responsibility:

* staff attendance and worked-time recording.

Relation:

* mandatory `staff -> StaffProfile`.

Relevant data:

* date;
* clock-in;
* clock-out;
* worked hours;
* status;
* notes.

### staff.LeaveRequest

Business responsibility:

* staff leave request and approval lifecycle.

Relations:

* mandatory `staff -> StaffProfile`;
* optional `approved_by -> accounts.User`.

Relevant data:

* request date;
* leave type;
* start date;
* end date;
* status;
* approval user;
* approval timestamp;
* notes.

### staff.StaffHistory

Business responsibility:

* record staff-related changes.

Relations:

* mandatory `staff -> StaffProfile`;
* optional `changed_by -> accounts.User`.

Relevant data:

* changes;
* note;
* inherited timestamps.

### website

The inspected application currently contains no demonstrated business model.

`website/models.py` contains no domain model.

The inspected website view contains no implemented business view.

No website URL contract was demonstrated by the inspected files.

No relation between `website` and `accounts.User` is currently demonstrated.

No website administration responsibility assigned to `SUPER_ADMIN` is currently demonstrated by code.

---

## Verified Domain Graph

```text
                         accounts.User
                               |
                               | OneToOne
                               v
                       staff.StaffProfile
                               |
          +--------------------+--------------------+
          |                    |                    |
          v                    v                    v
      Contract           WorkSchedule       AttendanceRecord
          |
          +-----------------------------------------+
                                                    |
                                                    v
                                               StaffProfile
                                                 manager
                                                    |
                                                    v
                                               StaffProfile

staff.StaffProfile
        |
        +---- LeaveRequest
        |          |
        |          +---- approved_by -> accounts.User
        |
        +---- StaffHistory
                   |
                   +---- changed_by -> accounts.User


accounts.User
        |
        +---- UserLoginHistory
        |
        +---- AuditLog


website
        |
        X
no implemented business relation demonstrated
```

---

## Verified Relations

### G1-R1 — User to StaffProfile

`StaffProfile.user` is a mandatory `OneToOneField` to `accounts.User`.

Therefore:

* one `StaffProfile` cannot belong to multiple users;
* one user cannot own multiple staff profiles through this relation;
* a `StaffProfile` cannot exist without a user;
* a `User` can currently exist without a `StaffProfile`.

This separation correctly distinguishes application identity from HR/professional identity.

### G1-R2 — Staff hierarchy

`StaffProfile.manager` references another `StaffProfile`.

The relation correctly models a professional hierarchy at the staff domain level rather than directly between authentication users.

### G1-R3 — Contracts

A staff member may own multiple contracts through `contracts`.

The current relation supports contractual history or successive contracts.

No database-level restriction limits a staff member to one active contract.

### G1-R4 — Work schedules

A staff member may own multiple schedule rows through `schedules`.

The structure supports multiple weekdays and multiple schedule records.

No uniqueness or overlap constraint is demonstrated.

### G1-R5 — Attendance

Attendance records belong to a staff profile.

No uniqueness constraint currently prevents multiple attendance records for the same staff member and date.

### G1-R6 — Leave requests

Leave requests belong to a staff profile.

Approval is attributed to an application user through `approved_by`.

The model does not currently constrain the role of the approving user.

### G1-R7 — Staff history

Staff history belongs to a staff profile.

The actor responsible for a change is represented by `changed_by`.

The relation preserves history if the acting user is removed because `SET_NULL` is used.

### G1-R8 — Login history

Login history may exist without a resolved user.

This is coherent with unsuccessful login tracking.

### G1-R9 — Audit log

Audit actions may remain after the acting user relation becomes unavailable because `SET_NULL` is used.

The audited object is represented generically by `model_name` and UUID `object_id`.

---

## Missing or Undefined Business Relations

### G1-M1 — Roles requiring StaffProfile

The current code does not define which internal roles must own a `StaffProfile`.

The following states are technically possible:

```text
DENTIST without StaffProfile
ASSISTANT without StaffProfile
RECEPTIONIST without StaffProfile
ACCOUNTANT without StaffProfile
ADMINISTRATOR without StaffProfile
SUPER_ADMIN without StaffProfile
```

The business requirement is undefined.

### G1-M2 — User account lifecycle to employment lifecycle

No explicit relation or synchronization rule exists between:

* `User.is_active`;
* `User.is_deleted`;
* `StaffProfile.status`;
* `StaffProfile.end_date`.

A staff member may therefore be professionally inactive while retaining an active application account.

The reverse contradiction is also possible.

### G1-M3 — Contract lifecycle to StaffProfile lifecycle

No rule connects:

* `Contract.status`;
* `Contract.start_date`;
* `Contract.end_date`;
* `StaffProfile.status`;
* `StaffProfile.hire_date`;
* `StaffProfile.end_date`.

A terminated staff profile may retain an apparently active contract.

An active staff profile may exist without an active contract.

Whether this is allowed is currently undefined.

### G1-M4 — Leave approver authority

`LeaveRequest.approved_by` accepts any `accounts.User`.

No business rule restricts approval to:

* a manager;
* an administrator;
* a super administrator;
* another explicitly authorized role.

### G1-M5 — StaffHistory and AuditLog responsibility

`StaffHistory` and `AuditLog` can both represent changes affecting staff data.

Their respective responsibilities are not explicitly defined.

Potential intended separation:

* `StaffHistory` = business HR history;
* `AuditLog` = technical/global audit trace.

This boundary must be formalized to avoid duplicate or inconsistent histories.

---

## Duplicated or Ambiguous Sources of Truth

### G1-D1 — Working schedule source

Two representations exist:

```text
StaffProfile.work_hours
WorkSchedule
```

`StaffProfile.work_hours` is an unrestricted JSON field.

`WorkSchedule` is a structured relational model containing:

* weekday;
* start time;
* end time;
* active state.

Both can represent staff working schedules.

The current code does not define which source is canonical.

This is a potential duplicated source of truth.

### G1-D2 — Salary source

Two salary values exist:

```text
StaffProfile.base_salary
Contract.salary
```

The current models do not define their semantic difference.

Possible interpretations include:

* `base_salary` as HR reference salary;
* `Contract.salary` as contractual salary.

This distinction is not demonstrated by the inspected code.

The two values can diverge without validation.

### G1-D3 — Employment state

Employment/account state is distributed across:

```text
User.is_active
User.is_deleted
StaffProfile.status
StaffProfile.end_date
Contract.status
Contract.end_date
```

These fields may represent different concepts, but their semantic boundaries and synchronization rules are currently undefined.

They therefore create an ambiguous lifecycle model.

---

## Business Invariants — Verified

### G1-I1

A `User` email is required when using `UserManager.create_user()`.

### G1-I2

A user created through `UserManager.create_user()` requires:

* first name;
* last name;
* valid role;
* password.

### G1-I3

A superuser created through `create_superuser()` is always assigned the `SUPER_ADMIN` role.

### G1-I4

A `StaffProfile` belongs to exactly one `User`.

### G1-I5

A `StaffProfile` requires an employee number.

### G1-I6

`employee_number` is globally unique.

### G1-I7

Contracts, schedules, attendance records, leave requests, and staff history require a staff profile.

---

## Business Invariants — Missing

### G1-I8

A manager must not manage their own `StaffProfile`.

Not enforced.

### G1-I9

The staff management graph must be acyclic.

Not enforced.

The following cycle is currently possible:

```text
A -> B
B -> A
```

Longer cycles are also possible.

### G1-I10

`StaffProfile.end_date` must not precede `hire_date`.

Not enforced.

### G1-I11

`Contract.end_date` must not precede `start_date`.

Not enforced.

### G1-I12

A work schedule end time must be after its start time.

Not enforced.

### G1-I13

Schedule records for the same staff member must follow a defined overlap policy.

Not defined or enforced.

### G1-I14

`weekday` must belong to a defined weekday range.

Not demonstrated by model choices or validators.

### G1-I15

Attendance `clock_out` must not precede `clock_in`.

Not enforced.

### G1-I16

`worked_hours` must follow a defined calculation or validation rule.

Not demonstrated.

The field may currently diverge from `clock_in` and `clock_out`.

### G1-I17

A leave request end date must not precede its start date.

Not enforced.

### G1-I18

Approved leave state must be coherent with `approved_by` and `approved_at`.

Not enforced.

The current model can represent contradictory states.

### G1-I19

Staff status must belong to an explicit business vocabulary.

Not enforced.

### G1-I20

Employment type must belong to an explicit business vocabulary.

Not enforced.

### G1-I21

Contract type and contract status must belong to explicit business vocabularies.

Not enforced.

### G1-I22

Attendance status must belong to an explicit business vocabulary.

Not enforced.

### G1-I23

Leave type and leave status must belong to explicit business vocabularies.

Not enforced.

### G1-I24

The business relationship between staff employment state and application access state must be explicit.

Not defined.

### G1-I25

The roles requiring a staff profile must be explicit.

Not defined.

---

## User Serializer Audit

`UserSerializer` exposes:

* id;
* email;
* password;
* first name;
* last name;
* phone;
* role;
* timezone;
* language;
* active state.

The serializer does not expose:

* `is_staff`;
* `is_superuser`;
* `is_deleted`;
* permission groups;
* individual permissions.

This prevents direct API assignment of Django administrative permission flags through this serializer.

### Creation behavior

Password is declared optional at field declaration level but is explicitly required by `create()`.

Creation delegates to:

```text
User.objects.create_user(...)
```

Therefore manager-level required-field and role validation is reused.

### Update behavior

The serializer directly assigns validated values to the instance.

It allows modification of:

* email;
* first name;
* last name;
* phone;
* role;
* timezone;
* language;
* `is_active`.

Password changes use `set_password()`.

### G1-S1 — Password validation

Password validation only rejects blank values.

No Django password validator invocation is demonstrated.

The serializer does not demonstrate enforcement of configured password strength policies.

### G1-S2 — Email normalization

The serializer lowercases email values.

`UserManager` uses `normalize_email()`.

The normalization strategy is therefore not exactly identical between serializer and manager paths.

The domain should define one canonical email normalization policy.

### G1-S3 — Role transitions

The serializer allows the `role` field to be updated.

No business validation defines allowed role transitions.

Examples currently not explicitly protected at serializer level include:

```text
DENTIST -> ACCOUNTANT
RECEPTIONIST -> ADMINISTRATOR
SUPER_ADMIN -> ASSISTANT
```

View permissions limit who may perform the update, but role-transition invariants remain undefined.

### G1-S4 — Active state transitions

The serializer allows `is_active` modification.

No synchronization with `StaffProfile.status`, `StaffProfile.end_date`, or contracts is performed.

### G1-S5 — Self-protection rules

No serializer invariant protects:

* the last active super administrator;
* super administrator demotion;
* super administrator deactivation.

The current view restricts mutation to a super administrator, but a super administrator may still perform a destructive administrative transition if no other service-level protection exists.

---

## Staff Serializer Audit

`StaffProfileSerializer` uses:

```text
fields = '__all__'
```

All model fields are exposed according to DRF model serializer behavior.

The inspected serializer defines no custom validation.

### G1-S6 — Employment date validation

No validation enforces:

```text
end_date >= hire_date
```

### G1-S7 — Manager self-reference

No validation rejects:

```text
staff.manager = staff
```

### G1-S8 — Management cycles

No validation detects management hierarchy cycles.

### G1-S9 — User lifecycle coherence

No validation checks:

* user activity;
* user soft-deletion state;
* user role;
* existing employment lifecycle state.

### G1-S10 — Status vocabulary

No serializer validation constrains `status` beyond the model field length.

### G1-S11 — Employment type vocabulary

No serializer validation constrains `employment_type`.

### G1-S12 — Work hours JSON

`work_hours` accepts the model JSON structure without a demonstrated domain schema.

The API contract for this JSON data is undefined.

### G1-S13 — Salary exposure

`base_salary` is exposed by the serializer.

Because the Staff view is accessible to `ADMINISTRATOR`, administrators can read and mutate salary data through this API.

This behavior must be an explicit authorization decision.

### G1-S14 — HR notes exposure

`notes` is exposed through the same serializer and permission boundary.

No field-level distinction exists between general professional data and potentially restricted HR data.

---

## User View and Permission Audit

`UserViewSet` uses:

```text
IsStaffMember
```

`IsStaffMember` accepts every currently defined internal role.

The permission helper requires:

* authenticated user;
* active user;
* non-deleted user;
* recognized internal role.

### Query visibility

`SUPER_ADMIN` can query all non-deleted users.

Every other internal role can query only its own user record.

This establishes the following read boundary:

```text
SUPER_ADMIN -> all internal users
OTHER STAFF -> own user identity only
```

### Mutation boundary

Only `SUPER_ADMIN` may:

* create users;
* update users;
* partially update users;
* delete users.

The current API therefore defines `SUPER_ADMIN` as the exclusive account lifecycle administrator.

### G1-V1 — User deletion behavior

`destroy()` delegates to `ModelViewSet.destroy()`.

The queryset excludes already soft-deleted users, but the inspected view does not itself demonstrate whether deletion invokes soft deletion or physical deletion.

The effective behavior depends on `SoftDeleteModel` implementation and must remain tied to the previously audited common model behavior.

No new conclusion beyond the actual `SoftDeleteModel` contract should be inferred.

### G1-V2 — Super administrator protection

No view-level protection prevents a super administrator from:

* deactivating their own account;
* changing their own role;
* deleting their own account;
* deactivating the last super administrator;
* demoting the last super administrator.

These lifecycle invariants are not demonstrated.

### G1-V3 — HTTP method permission duplication

Mutation authorization is implemented separately in:

* `create`;
* `update`;
* `partial_update`;
* `destroy`.

The behavior is explicit but authorization policy is distributed across method overrides rather than represented as a dedicated action-aware permission policy.

This is a technical maintainability finding, not by itself a domain incoherence.

---

## Staff View and Permission Audit

`StaffProfileViewSet` is a full `ModelViewSet`.

It exposes CRUD operations for `StaffProfile`.

Permission:

```text
IsAdministrator
```

Authorized roles are:

* `SUPER_ADMIN`;
* `ADMINISTRATOR`.

The current API therefore grants both roles full StaffProfile CRUD access.

### G1-V4 — Administrator HR authority

`ADMINISTRATOR` can read and mutate all exposed StaffProfile fields, including:

* employee number;
* hire date;
* end date;
* department;
* job title;
* employment type;
* manager;
* work hours;
* base salary;
* status;
* notes.

The current domain therefore effectively treats `ADMINISTRATOR` as a full staff-profile administrator.

This authority is not explicitly documented in the inspected domain documentation.

### G1-V5 — Account and HR authority asymmetry

An `ADMINISTRATOR` can modify `StaffProfile`.

An `ADMINISTRATOR` cannot modify `User`.

Therefore the following divergence can be created:

```text
StaffProfile.status = inactive
User.is_active = True
```

The administrator cannot directly reconcile the application account state.

The business lifecycle boundary between HR administration and account administration is undefined.

### G1-V6 — No object-level staff restrictions

No object-level permission rule is demonstrated.

Authorized administrators can operate on every StaffProfile returned by the unrestricted queryset.

### G1-V7 — Related HR models

Only `StaffProfileViewSet` was demonstrated in the inspected staff view.

No API view was demonstrated for:

* `Contract`;
* `WorkSchedule`;
* `AttendanceRecord`;
* `LeaveRequest`;
* `StaffHistory`.

Their API lifecycle and authorization policy are therefore not established by the inspected staff view.

---

## Website Domain Audit

The currently inspected `website` application does not demonstrate a business administration domain.

No website configuration model was observed.

No public content model was observed.

No website administration model was observed.

No implemented website business view was observed.

No website URL contract was observed.

No permission relation with `SUPER_ADMIN` was observed.

### G1-W1

The previous conceptual graph linking `SUPER_ADMIN` to website administration is not supported by the inspected implementation.

### G1-W2

`website` must currently be treated as an application scaffold or incomplete domain boundary.

### G1-W3

No website administration invariant can be validated until an implemented domain model or explicit architecture contract exists.

---

## Proposed Domain Decisions

All decisions below are `PROPOSED` until the G1-G13 global coherence scan confirms, revises, or rejects them.

### G1-P1 — Canonical internal identity

Status: `PROPOSED`

`accounts.User` remains the canonical source of truth for internal authenticated application identity.

Patients and public visitors must remain outside this model unless a future authentication domain explicitly introduces a separate identity architecture.

### G1-P2 — Canonical staff identity

Status: `PROPOSED`

`staff.StaffProfile` remains the canonical source of truth for professional and HR staff identity.

Authentication fields must remain in `User`.

HR and professional fields must remain in `StaffProfile` or dedicated staff subdomains.

### G1-P3 — Roles requiring StaffProfile

Status: `PROPOSED`

The following operational roles should require a `StaffProfile`:

* `DENTIST`;
* `ASSISTANT`;
* `RECEPTIONIST`;
* `ACCOUNTANT`.

`SUPER_ADMIN` should not automatically require a `StaffProfile` because it may represent a platform-level administrative identity.

`ADMINISTRATOR` requires a final business decision because the role may represent either an operational clinic employee or a platform/clinic administrative identity.

This proposal must be checked against all role usage during G2-G13.

### G1-P4 — Separate employment state from application access

Status: `PROPOSED`

Employment state and application access state must remain distinct concepts.

Canonical responsibilities:

```text
StaffProfile / Contract
    -> employment lifecycle

User.is_active / User.is_deleted
    -> application access lifecycle
```

However, explicit synchronization rules must exist.

Proposed rule:

```text
employment termination
    -> application access must be reviewed or disabled

application deactivation
    -/-> automatic employment termination
```

Automatic behavior must not be implemented before cross-domain workflow and notification review.

### G1-P5 — Canonical structured work schedule

Status: `PROPOSED`

`WorkSchedule` should become the canonical source of truth for structured staff working schedules.

`StaffProfile.work_hours` should not remain a parallel writable schedule source.

Before removal or deprecation, G3 Scheduling must determine whether appointment availability is identical to staff work schedules or requires a separate clinical availability concept.

### G1-P6 — Distinguish contractual schedule from clinical availability

Status: `PROPOSED`

G1 defines `WorkSchedule` as a candidate source for contractual or normal staff working time.

G3 must determine whether dentists require a separate clinical availability model for appointment scheduling.

No assumption that HR schedule equals appointment availability is accepted.

### G1-P7 — Canonical salary responsibility

Status: `PROPOSED`

`Contract.salary` should be the canonical contractual salary value.

`StaffProfile.base_salary` must either:

* receive an explicit distinct business meaning; or
* be removed as a duplicated source of truth.

Until a distinct business definition is demonstrated, `base_salary` is considered redundant or ambiguous.

### G1-P8 — Explicit HR vocabularies

Status: `PROPOSED`

The following fields require explicit domain vocabularies using model choices or equivalent domain validation:

* `StaffProfile.employment_type`;
* `StaffProfile.status`;
* `Contract.contract_type`;
* `Contract.status`;
* `AttendanceRecord.status`;
* `LeaveRequest.leave_type`;
* `LeaveRequest.status`.

The exact values must be defined during remediation from actual clinic workflow requirements.

Arbitrary strings must not remain the long-term domain contract.

### G1-P9 — Acyclic management hierarchy

Status: `PROPOSED`

The management hierarchy must enforce:

```text
manager != self
```

and must reject direct and indirect management cycles.

### G1-P10 — Employment date coherence

Status: `PROPOSED`

The staff domain must enforce:

```text
StaffProfile.end_date >= StaffProfile.hire_date
Contract.end_date >= Contract.start_date
LeaveRequest.end_date >= LeaveRequest.start_date
```

when an end date exists.

### G1-P11 — Work schedule coherence

Status: `PROPOSED`

`WorkSchedule` must enforce:

* valid weekday values;
* `end_time > start_time`;
* an explicit overlap policy for active schedules belonging to the same staff member.

The final overlap policy must be checked against G3 Scheduling.

### G1-P12 — Attendance coherence

Status: `PROPOSED`

Attendance records must enforce:

```text
clock_out >= clock_in
```

when both timestamps exist.

The domain must define whether `worked_hours` is:

* calculated data;
* cached calculated data;
* manually entered authoritative data.

A duplicated writable source between timestamps and `worked_hours` must not remain undefined.

### G1-P13 — Leave approval lifecycle

Status: `PROPOSED`

Leave approval must define explicit state transitions.

Approved or rejected states must be coherent with:

* `approved_by`;
* `approved_at`.

The approving actor must satisfy an explicit authorization rule.

The manager hierarchy and administrator roles must be considered before choosing the final approver policy.

### G1-P14 — StaffHistory versus AuditLog

Status: `PROPOSED`

Responsibilities should be separated as follows:

```text
StaffHistory
    = business-readable HR history

AuditLog
    = global technical and security audit trace
```

The same event may create both records only when each record serves its distinct responsibility.

Neither model should be treated as an interchangeable source of truth.

### G1-P15 — Salary and HR notes authorization

Status: `PROPOSED`

Salary and restricted HR notes must not inherit general staff-profile visibility by accident.

The API should explicitly define whether `ADMINISTRATOR` has HR-sensitive-data authority.

If not, serializer separation or field-level authorization will be required.

### G1-P16 — User role transition policy

Status: `PROPOSED`

User role transitions require explicit invariants.

At minimum, remediation must evaluate:

* last super administrator protection;
* self-demotion;
* self-deactivation;
* self-deletion;
* operational role transitions affecting required staff profiles.

### G1-P17 — Password policy reuse

Status: `PROPOSED`

User creation and password update APIs should use the configured Django password validation policy rather than only checking for a non-empty password.

### G1-P18 — Canonical email normalization

Status: `PROPOSED`

Email normalization must use one canonical policy across:

* manager creation;
* serializer creation;
* serializer update.

### G1-P19 — Website administration boundary

Status: `PROPOSED`

Website administration must not currently be represented as an established G1 business relation.

Until implementation is demonstrated:

```text
website administration = UNDEFINED / NOT IMPLEMENTED
```

If website configuration or content administration is introduced later, its ownership and permissions must be explicitly attached to the relevant administrative role.

---

## Expected Remediation Candidates

The following are remediation candidates only. No code modification belongs to the G1-G13 review phase.

1. Define role-to-StaffProfile requirements.
2. Define account-access and employment-lifecycle synchronization rules.
3. Add explicit HR domain vocabularies.
4. Add staff and contract date invariants.
5. Reject manager self-reference and hierarchy cycles.
6. Decide the canonical work-schedule source after G3.
7. Remove or redefine `StaffProfile.work_hours`.
8. Define `base_salary` semantics or remove it in favor of `Contract.salary`.
9. Define attendance worked-hours authority.
10. Define leave approval transitions and approver authority.
11. Separate HR history responsibility from global audit responsibility.
12. Add StaffProfile serializer business validation.
13. Review sensitive salary and HR-note exposure.
14. Define user role-transition invariants.
15. Protect the last active super administrator.
16. Apply Django password validation to API password operations.
17. Unify email normalization.
18. Decide whether `ADMINISTRATOR` is an HR-sensitive-data administrator.
19. Review API exposure for Contract, WorkSchedule, AttendanceRecord, LeaveRequest, and StaffHistory.
20. Remove the unsupported website-administration relation from the validated domain graph until implementation exists.

---

## Cross-Domain Dependencies

### G2 — Patient Core

Must verify whether patient ownership, assignment, or clinic responsibility references `User` directly or requires `StaffProfile`.

Dentist identity references must distinguish authentication identity from professional staff identity.

### G3 — Scheduling

Must review:

* dentist availability;
* staff working schedules;
* `WorkSchedule`;
* `StaffProfile.work_hours`;
* leave;
* inactive staff;
* terminated staff.

G3 must confirm or revise G1-P5 and G1-P6.

### G4 — Odontogram

Must verify how the acting dentist or clinical staff member is represented.

### G5 — Treatment Planning

Must verify dentist ownership, authorship, approval, and assignment relations.

### G6 — Clinical Treatment

Must verify clinical actor identity and whether professional identity requires `StaffProfile`.

### G7 — Billing

Must verify accountant role usage and whether accounting staff require StaffProfile.

### G8 — Inventory

Must verify staff actors responsible for stock movements and whether generic User references are sufficient.

### G9 — Prescriptions

Must verify prescriber identity.

A prescription may require professional dentist identity beyond generic authenticated User identity.

### G10 — Imaging

Must verify uploader, requester, reviewer, and clinical actor relations.

### G11 — Document Management

Must verify document ownership, creator identity, and audit actor semantics.

### G12 — Notifications & Workflow

Must verify employment termination, account deactivation, leave approval, and role-change workflow impacts.

G12 is directly relevant to G1-P4 and G1-P13.

### G13 — Reporting & Global Read Domain

Must review:

* `AuditLog`;
* `UserLoginHistory`;
* `StaffHistory`;
* sensitive HR data visibility;
* global administrative read boundaries.

---

## Open Conflicts for Global Coherence Scan

The following decisions must remain visible during G2-G13:

```text
G1-C1
Should operational domain models reference User or StaffProfile
when professional identity is required?

G1-C2
Is WorkSchedule an HR schedule only or also a clinical
appointment availability source?

G1-C3
Does ADMINISTRATOR have full HR-sensitive-data authority?

G1-C4
Which roles are required to own StaffProfile?

G1-C5
What event controls application access after employment termination?

G1-C6
Is StaffProfile.base_salary a distinct business concept or duplicate data?

G1-C7
Who may approve leave requests?

G1-C8
Which events belong to StaffHistory, AuditLog, or both?

G1-C9
Does worked_hours remain stored or become derived?

G1-C10
Will website administration become a real domain or remain outside
the current backend business architecture?
```

---

## G1 Final Domain Verdict

The fundamental separation between internal application identity and professional staff identity is coherent.

Validated core architecture:

```text
accounts.User
    = internal authenticated identity

staff.StaffProfile
    = professional and HR staff identity

Patient
    != User

Public visitor
    != User
```

The current implementation nevertheless contains undefined lifecycle rules, ambiguous sources of truth, missing HR invariants, unrestricted business vocabularies, and unresolved authorization boundaries.

No immediate model removal or relation rewrite is approved during G1.

The proposed decisions G1-P1 to G1-P19 are retained for cross-domain validation during G2-G13.

The conflicts G1-C1 to G1-C10 must be checked explicitly against subsequent domains.

`website` is not currently accepted as an implemented website administration domain.

G1 review is complete.

Status: `DONE`
