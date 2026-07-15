# Backend Security Audit

**Project:** Dental Clinic  
**Audit type:** Evidence-based repository security assessment  
**Reference commit:** `a56e7099ccc015f9b5215314f312846196140022`  
**Audit date:** 2026-07-15  
**Status:** IN PROGRESS

## Audit discipline

This document is built incrementally from repository evidence.

No finding is accepted from a previous audit without revalidation against the current codebase.

Each finding must contain:

- classification;
- severity;
- status;
- repository evidence;
- security consequence;
- required remediation.

No remediation is applied during the audit phase.

---

## SEC-001 — Patient-linked documents are exposed to every staff role

**Classification:** CONFIRMED VULNERABILITY  
**Severity:** P0  
**Status:** OPEN

### Evidence

`documents/views.py` defines `DocumentViewSet` with:

- `queryset = Document.objects.all()`;
- `permission_classes = [IsStaffMember]`.

`accounts/permissions.py` defines `IsStaffMember` using all values from `User.Role.values`.

The accepted role set therefore includes non-clinical staff roles such as receptionist and accountant.

`documents/models.py` defines `Document.patient` as a direct foreign key to `patients.Patient`.

`documents/serializers.py` exposes all `Document` model fields through `fields = '__all__'`.

`documents/urls.py` registers `DocumentViewSet` on the DRF router.

`dental_clinic/urls.py` includes `documents.urls` under the `/api/` boundary.

No role-based queryset scoping or object-level authorization for `Document` was evidenced in the inspected repository paths.

### Security consequence

Every active staff role accepted by `IsStaffMember` can reach the complete patient-linked `Document` queryset through the API.

The current authorization boundary does not distinguish clinical staff from receptionist or accountant roles for patient documents.

The document domain also models confidential attachments through `DocumentAttachment.is_confidential`. However, direct API exposure of confidential attachments is not claimed by this finding because no `DocumentAttachmentViewSet` was evidenced in the inspected router configuration.

### Required remediation

Define and document the document-access authorization matrix before changing the code.

The matrix must explicitly define access by:

- role;
- API action;
- patient scope;
- document type;
- document ownership or creator relationship, if applicable;
- confidentiality state where attachments are involved.

Then:

1. replace unrestricted `Document.objects.all()` exposure with an explicitly scoped queryset policy;
2. replace generic `IsStaffMember` authorization with a document-specific permission boundary;
3. enforce object-level authorization for retrieve, update, partial update, and destroy actions;
4. define the confidentiality policy for `DocumentAttachment`;
5. add authorization characterization tests for every role and relevant action;
6. verify that list endpoints cannot disclose unauthorized patient document metadata.

### Required validation evidence

Remediation is not complete until tests prove:

- super admin access according to policy;
- administrator access according to policy;
- dentist access according to patient/document scope;
- assistant access according to policy;
- receptionist denial or explicitly limited access;
- accountant denial or explicitly limited access;
- cross-patient document access is rejected where the policy forbids it;
- unauthorized list results do not contain protected document metadata.

---



## SEC-002 — Clinical file upload boundaries lack evidenced file validation

**Classification:** SECURITY GAP  
**Severity:** P0  
**Status:** OPEN

### Evidence

`documents/models.py` defines file storage fields through:

- `Document.pdf_file`;
- `DocumentAttachment.file`.

Both fields use Django `FileField` without repository-evidenced file validators.

`imaging/models.py` defines:

- `ImagingInstance.file`;
- `ImagingInstance.thumbnail`.

These fields also use `FileField` without repository-evidenced file validators.

`imaging/serializers.py` exposes all `ImagingInstance` model fields through `fields = '__all__'` and defines no file-specific validation method.

`imaging/views.py` exposes `ImagingInstanceViewSet` as a writable `ModelViewSet`.

`imaging/urls.py` registers the imaging instance ViewSet on the DRF router.

`dental_clinic/settings.py` defines `MEDIA_URL` and `MEDIA_ROOT` but does not evidence an application-level clinical upload policy for file size or accepted content.

Repository-wide inspection did not evidence:

- file extension validators;
- MIME-type validation;
- file-signature or magic-byte validation;
- clinical file size limits;
- malformed document or image rejection;
- malware scanning or quarantine controls.

### Security consequence

The current application boundary does not prove that uploaded clinical documents and imaging files are restricted to expected file formats or bounded file sizes.

A client reaching a writable upload endpoint may submit content whose filename, declared type, actual content, or size does not match the intended clinical file policy.

For imaging records, the writable `ImagingInstanceViewSet` provides a directly evidenced API upload boundary.

For `Document.pdf_file`, the writable `DocumentViewSet` exposes the model field through the serializer.

Direct API exposure of `DocumentAttachment.file` is not claimed because no `DocumentAttachmentViewSet` was evidenced in the inspected router configuration.

This finding does not claim remote code execution, malware execution, or public media exposure. Those consequences require separate runtime and deployment evidence.

### Required remediation

Define a centralized clinical file upload policy before modifying individual serializers or models.

The policy must explicitly define:

- accepted file formats by domain field;
- maximum file size by file category;
- allowed filename handling;
- extension validation;
- declared MIME-type validation;
- server-side content or file-signature validation;
- malformed file rejection;
- storage naming policy;
- quarantine or malware-scanning requirements;
- logging and audit requirements for rejected uploads.

Then:

1. implement reusable server-side file validators;
2. apply validators to document and imaging upload boundaries;
3. enforce serializer-level validation where request context or field-specific policy is required;
4. ensure file validation occurs before a file is accepted as a valid clinical domain record;
5. define a dedicated validation policy for DICOM or other medical imaging formats if those formats are supported;
6. prevent client-controlled `file_type` values from being treated as proof of actual file content;
7. add upload security characterization tests.

### Required validation evidence

Remediation is not complete until tests prove:

- an allowed document file is accepted;
- an allowed imaging file is accepted;
- an oversized file is rejected;
- a forbidden extension is rejected;
- a mismatched extension and content type is rejected;
- a mismatched declared MIME type and actual file content is rejected;
- malformed supported files are rejected where structural validation is required;
- rejected files do not create valid clinical domain records;
- rejected upload attempts produce the required audit evidence;
- DICOM-specific validation is enforced if DICOM upload is supported.

---


## SEC-003 — Login endpoint lacks evidenced brute-force protection

**Classification:** SECURITY GAP  
**Severity:** P1  
**Status:** OPEN

### Evidence

`accounts/urls.py` exposes `LoginView` through `/api/auth/login/`.

`accounts/views/auth.py` defines `LoginView` with:

- `authentication_classes = []`;
- `permission_classes = [AllowAny]`.

The login view does not define a DRF throttle class.

`accounts/services/authentication.py` delegates credential verification to Django authentication and records failed authentication attempts through `log_login_attempt()`.

`accounts/services/login_history.py` persists login attempts in `UserLoginHistory`, including:

- source IP;
- user agent;
- success or failure state.

However, the inspected authentication flow does not query login history before authentication to enforce:

- an attempt threshold;
- temporary lockout;
- progressive delay;
- account-based rate limiting;
- IP-based rate limiting.

`dental_clinic/settings.py` does not define `DEFAULT_THROTTLE_CLASSES` or `DEFAULT_THROTTLE_RATES`.

Repository inspection did not evidence an alternative middleware or authentication backend enforcing login brute-force protection.

### Security consequence

The application records failed login attempts but does not evidence an active control that limits repeated authentication attempts.

An attacker reaching the login endpoint may repeatedly submit credentials without an application-enforced attempt threshold, cooldown period, or DRF rate limit.

The existing `UserLoginHistory` provides audit evidence but does not itself prevent brute-force or credential-stuffing attempts.

This finding does not claim successful account compromise. It identifies the absence of an evidenced preventive control at the login boundary.

### Required remediation

Define a dedicated authentication abuse-protection policy before modifying the login flow.

The policy must explicitly define:

- rate-limit scope;
- IP-based controls;
- account or normalized-email-based controls;
- failed-attempt threshold;
- observation window;
- cooldown or temporary lockout duration;
- progressive delay requirements, if used;
- successful-login reset behavior;
- trusted proxy and client-IP handling;
- audit requirements;
- user enumeration constraints.

Then:

1. apply a dedicated throttle or equivalent preventive control to the login endpoint;
2. enforce account-aware protection in addition to IP-only protection where required;
3. preserve a generic authentication failure response;
4. define safe client-IP extraction behind trusted proxies;
5. prevent attacker-controlled forwarding headers from being treated as authoritative without proxy trust configuration;
6. retain failed-attempt audit evidence;
7. add brute-force protection characterization tests.

### Required validation evidence

Remediation is not complete until tests prove:

- normal login attempts remain available;
- repeated failed attempts trigger the defined protection threshold;
- protection applies according to the documented IP policy;
- protection applies according to the documented account or normalized-email policy;
- changing only the email does not trivially bypass an IP-scoped control;
- changing only the source IP does not trivially bypass an account-scoped control where account protection is required;
- a successful login resets or updates failure state according to policy;
- the cooldown or lockout expires according to policy;
- inactive and soft-deleted accounts do not disclose account existence;
- throttled and invalid authentication responses do not create a user-enumeration distinction;
- failed and blocked attempts produce the required audit evidence;
- forwarded client IP headers are trusted only according to deployment policy.

---
## SEC-004 — Authentication tokens are persistent and reused across login events

**Classification:** SECURITY GAP  
**Severity:** P1  
**Status:** OPEN

### Evidence

`accounts/services/authentication.py` defines `issue_token_for_user()` using:

- `Token.objects.get_or_create(user=user)`;
- `return token.key`.

The service explicitly returns an existing token when one already exists for the user.

`login_with_token()` calls `issue_token_for_user()` after successful authentication.

`accounts/views/auth.py` returns the resulting token key to the client in the login response.

The inspected authentication flow does not evidence:

- token expiration;
- token age validation;
- token rotation on successful login;
- token rotation after credential changes;
- per-device or per-session token isolation;
- an absolute token lifetime;
- an inactivity lifetime.

`dental_clinic/settings.py` configures DRF `TokenAuthentication`.

`accounts/views/auth.py` does provide explicit token revocation on logout through:

`Token.objects.filter(user=request.user).delete()`.

Therefore, this finding does not claim that token revocation is entirely absent. Explicit logout revokes the current user token.

### Security consequence

A successful login can return a previously issued persistent authentication token instead of creating a fresh authentication credential.

If a token is exposed and the legitimate user continues authenticating without explicitly logging out, subsequent login events do not evidence automatic invalidation or rotation of the exposed token.

The effective lifetime of the token is therefore not bounded by an evidenced expiration policy.

Because the standard token model provides one token per user in the inspected flow, separate device or session credentials are not evidenced.

This finding does not claim that tokens are publicly exposed by the repository. It identifies weak lifecycle control after token issuance.

### Required remediation

Define the API authentication credential lifecycle before replacing the current implementation.

The policy must explicitly define:

- authentication mechanism;
- credential lifetime;
- absolute expiration;
- inactivity expiration, if required;
- rotation behavior;
- logout revocation behavior;
- password-change revocation behavior;
- administrator-forced revocation;
- lost-device or compromised-token response;
- concurrent device or session policy;
- credential storage expectations for the React client.

Then:

1. select an authentication mechanism that supports the documented lifecycle;
2. stop treating an existing persistent token as indefinitely reusable authentication state;
3. enforce server-side credential expiration;
4. define credential rotation according to policy;
5. revoke active credentials after security-sensitive account events;
6. provide an administrative revocation path where required;
7. define frontend credential storage and renewal behavior;
8. add authentication lifecycle characterization tests.

### Required validation evidence

Remediation is not complete until tests prove:

- successful authentication issues credentials according to the documented policy;
- expired credentials are rejected;
- credential lifetime is enforced server-side;
- rotation occurs according to policy;
- old credentials are rejected after required rotation;
- logout revokes the relevant credential or session;
- password changes revoke credentials according to policy;
- administrator-forced revocation invalidates targeted credentials;
- concurrent device or session behavior matches the documented policy;
- a new login does not silently preserve a compromised credential beyond the permitted lifecycle;
- inactive and soft-deleted users cannot continue authenticating with credentials contrary to policy;
- the React client authentication flow matches the backend credential lifecycle.

---

## SEC-005 — Production Django transport and cookie security policy is not evidenced

**Classification:** SECURITY GAP  
**Severity:** P1  
**Status:** OPEN

### Evidence

`dental_clinic/settings.py` includes Django `SecurityMiddleware`.

Therefore, this finding does not claim that Django security middleware is absent.

However, the inspected settings do not define an explicit production policy for:

- `SECURE_SSL_REDIRECT`;
- `SECURE_HSTS_SECONDS`;
- `SECURE_HSTS_INCLUDE_SUBDOMAINS`;
- `SECURE_HSTS_PRELOAD`;
- `SESSION_COOKIE_SECURE`;
- `CSRF_COOKIE_SECURE`;
- `SECURE_PROXY_SSL_HEADER`.

Repository-wide inspection did not evidence an alternative production settings module defining these controls.

`docker-compose.yml` starts the Django application with:

`python manage.py runserver 0.0.0.0:8000`

The inspected Compose configuration does not evidence:

- a production WSGI or ASGI application server;
- an HTTPS reverse proxy;
- a TLS termination boundary.

`.env.example` defines `DEBUG=True` and development-oriented host values.

No separate repository-evidenced production environment example or production security configuration was identified in the inspected paths.

### Security consequence

The repository does not currently prove that a production deployment will enforce HTTPS redirection, secure cookie transport, or HTTP Strict Transport Security.

If the current settings are reused in a production environment without an external control layer, transport security may depend on undocumented infrastructure behavior.

Session and CSRF cookies are not repository-evidenced as restricted to secure HTTPS transport.

The application also does not evidence how Django determines the original HTTPS scheme when deployed behind a trusted reverse proxy.

This finding does not claim that a currently deployed production instance is serving traffic over plain HTTP. No production deployment state was inspected.

The finding is limited to the absence of a repository-evidenced production security policy.

### Required remediation

Define the production deployment trust boundary before enabling transport security settings.

The policy must explicitly define:

- where TLS terminates;
- whether Django is directly internet-facing;
- the trusted reverse proxy architecture;
- forwarded protocol header handling;
- HTTPS redirect ownership;
- HSTS ownership and duration;
- secure session cookie requirements;
- secure CSRF cookie requirements;
- development and production settings separation;
- production application server requirements.

Then:

1. create an explicit production settings boundary or equivalent environment-driven security policy;
2. enforce HTTPS redirection at the documented layer;
3. enable secure session cookies in production;
4. enable secure CSRF cookies in production;
5. configure HSTS only after HTTPS coverage is verified;
6. configure `SECURE_PROXY_SSL_HEADER` only when a trusted proxy strips and sets the authoritative forwarded protocol header;
7. replace Django `runserver` for production execution with a supported production WSGI or ASGI server;
8. document the TLS termination and proxy trust model;
9. add production security configuration validation.

### Required validation evidence

Remediation is not complete until evidence proves:

- production `DEBUG` is disabled;
- production HTTPS requests are recognized correctly by Django;
- plain HTTP requests are redirected or rejected according to policy;
- session cookies carry the `Secure` attribute in production;
- CSRF cookies carry the `Secure` attribute in production;
- HSTS is emitted according to the documented production policy;
- HSTS is not enabled prematurely on an environment without complete HTTPS coverage;
- forwarded protocol headers are trusted only from the documented proxy boundary;
- attacker-supplied forwarding headers cannot independently mark an insecure request as trusted HTTPS;
- the production process does not use Django `runserver`;
- development settings remain usable without silently weakening production policy;
- Django deployment checks pass according to the production configuration.

---


## SEC-006 — Django can start with a known static SECRET_KEY fallback

**Classification:** CONFIRMED VULNERABILITY  
**Severity:** P1  
**Status:** OPEN

### Evidence

`dental_clinic/settings.py` defines the Django secret key through environment-driven configuration with a static fallback value:

`changeme`

The inspected settings therefore permit application startup without an explicitly supplied deployment secret.

`docker-compose.yml` injects `SECRET_KEY` from the environment into the web service.

However, the Django settings module itself does not require the secret to be present.

Application execution outside the inspected Compose environment, or execution with incomplete environment configuration, can therefore fall back to the known static key.

`.env.example` documents a placeholder value and does not contain an observed production secret.

This finding does not claim that a real production secret is committed to the repository.

### Security consequence

Django cryptographic signing security depends on `SECRET_KEY` remaining secret and unpredictable.

A deployment that starts with the known fallback value uses a repository-evidenced predictable signing secret.

This can undermine security properties that rely on Django signing mechanisms.

The presence of environment injection in Docker Compose does not eliminate the unsafe fallback because the settings module still accepts startup without a deployment-provided secret.

This finding does not claim that the currently running development or production environment is using `changeme`.

The confirmed vulnerability is the code path that permits startup with a known static secret.

### Required remediation

Make `SECRET_KEY` a mandatory runtime secret.

Then:

1. remove the static `changeme` fallback;
2. fail application startup when `SECRET_KEY` is absent;
3. fail startup when the configured value matches a documented placeholder or forbidden development value;
4. define secret provisioning separately for development, test, and production environments;
5. keep real secret values outside version control;
6. define a production secret rotation procedure;
7. document the operational impact of secret rotation on Django-signed data;
8. add configuration validation tests.

### Required validation evidence

Remediation is not complete until evidence proves:

- application startup fails when `SECRET_KEY` is absent;
- application startup fails when a forbidden placeholder value is supplied;
- development startup succeeds with an explicitly provisioned development secret;
- test execution receives an explicit test secret;
- production configuration requires an externally provisioned secret;
- no real deployment secret is tracked by Git;
- Docker startup does not silently substitute a known fallback;
- Django deployment checks run against the intended production configuration;
- the secret rotation procedure documents the effect on signed application data.

---

## SEC-007 — API user creation and password update do not enforce Django password validators

**Classification:** SECURITY GAP  
**Severity:** P1  
**Status:** OPEN

### Evidence

`accounts/serializers.py` defines `UserSerializer.validate_password()`.

The validation logic:

- strips the submitted password;
- rejects an empty resulting value.

The serializer does not call Django `validate_password()` or otherwise evidence enforcement of the configured Django password validators.

`UserSerializer.create()` passes the password to `User.objects.create_user()`.

`accounts/models.py` defines `UserManager.create_user()`.

The manager verifies that a password is present and then calls:

`user.set_password(password)`

`UserSerializer.update()` also applies a supplied password through:

`instance.set_password(password)`

Django `set_password()` hashes the supplied credential but does not itself enforce Django password validation policy.

`accounts/views/users.py` exposes user creation, update, and partial update through `UserViewSet`.

The ViewSet restricts these write operations to the `SUPER_ADMIN` role.

Therefore, this finding does not claim anonymous or general staff account creation.

Repository inspection did not evidence password-validator enforcement at the serializer, service, or manager boundaries used by this API flow.

### Security consequence

The API account-management boundary can accept a non-empty password without proving that the password satisfies the configured Django password policy.

A super administrator can therefore create or update an account with a weak credential that Django password validators would otherwise reject.

Password hashing remains enforced through `set_password()`.

The weakness is policy validation before credential storage, not plaintext password storage.

Restricting account management to the super administrator reduces exposure but does not replace password-strength enforcement.

### Required remediation

Define a single password validation policy for every account credential creation and change boundary.

Then:

1. invoke Django password validation before accepting a new password;
2. provide the target user instance to password validation where user-attribute similarity checks require it;
3. enforce the same policy during API account creation;
4. enforce the same policy during API password update;
5. verify superuser creation and administrative account-management boundaries;
6. prevent serializers, managers, or future services from silently bypassing the policy;
7. return controlled validation errors without exposing sensitive credential data;
8. add password-policy characterization tests.

### Required validation evidence

Remediation is not complete until tests prove:

- a compliant password is accepted;
- a password below the configured minimum length is rejected;
- a common password is rejected;
- an entirely numeric password is rejected;
- a password too similar to relevant user attributes is rejected according to configured validators;
- API user creation enforces the password policy;
- full API user update enforces the password policy when changing a password;
- partial API user update enforces the password policy when changing a password;
- password validation errors do not include the submitted password;
- accepted passwords remain hashed through Django password handling;
- super administrator privileges do not bypass the password policy;
- all documented credential creation and change boundaries apply the same policy.

---


## SEC-008 — Backend container does not enforce a non-root runtime identity

**Classification:** HARDENING  
**Severity:** P1  
**Status:** OPEN

### Evidence

The repository root `Dockerfile` uses:

`python:3.12-slim`

The Dockerfile does not create a dedicated application user or group.

No Dockerfile `USER` instruction is defined before the entrypoint or application command.

The image therefore does not evidence an explicit non-root runtime identity for the backend application.

`docker/entrypoint.sh` executes:

- the PostgreSQL availability check;
- Django migrations;
- Django static collection;
- the final application process.

The entrypoint does not evidence a privilege-drop mechanism before executing the application process.

`docker-compose.yml` does not define an explicit `user` for the `web` service.

The inspected Compose service also does not evidence:

- `cap_drop`;
- `security_opt` with `no-new-privileges`;
- a read-only root filesystem.

The development Compose configuration bind-mounts the repository root into `/app`.

Repository-wide inspection did not evidence an alternative backend container definition enforcing a dedicated runtime user.

### Security consequence

The backend container does not prove least-privilege execution at the operating-system identity boundary.

If an application-level compromise reaches operating-system execution inside the container, the compromised process may inherit the container's default elevated identity and broader write access than a dedicated application user would require.

The repository bind mount used by the development Compose service also gives the container process access to the mounted application tree according to host and Docker mount permissions.

This finding does not claim container escape, host compromise, or an existing remote code execution vulnerability.

It identifies the absence of repository-evidenced container least-privilege controls.

### Required remediation

Define separate development and production container privilege requirements before modifying the image.

The policy must explicitly define:

- runtime user and group;
- required filesystem ownership;
- writable application paths;
- media storage permissions;
- static collection ownership;
- migration execution ownership;
- bind-mount policy;
- Linux capability requirements;
- privilege-escalation restrictions;
- read-only filesystem feasibility.

Then:

1. create a dedicated non-root application user and group in the backend image;
2. assign only required application paths to that identity;
3. run the application process as the dedicated non-root user;
4. verify migration and static collection requirements without broad root runtime privileges;
5. separate development bind-mount behavior from production container configuration;
6. drop unnecessary Linux capabilities where supported;
7. enable `no-new-privileges` where compatible with the deployment model;
8. evaluate a read-only root filesystem with explicit writable mounts for required runtime data;
9. add container runtime security validation.

### Required validation evidence

Remediation is not complete until evidence proves:

- the backend application process runs as a non-root UID;
- the application starts successfully with the dedicated runtime identity;
- database migrations execute according to the documented deployment policy;
- static collection executes according to the documented deployment policy;
- required media paths remain writable;
- application source paths are not writable in production unless explicitly required;
- unnecessary Linux capabilities are removed according to policy;
- privilege escalation is restricted according to policy;
- development bind mounts are not silently inherited by the production deployment definition;
- container restart and deployment workflows remain functional;
- the production image does not require root privileges for normal application request handling.

---

## SEC-009 — Python dependencies are not reproducibly locked

**Classification:** HARDENING  
**Severity:** P1  
**Status:** OPEN

### Evidence

The repository root `requirements.txt` declares:

- `Django>=4.2`;
- `psycopg2-binary`;
- `django-environ`;
- `djangorestframework`;
- `django-cors-headers==4.8.0`.

Only `django-cors-headers` is pinned to an exact version.

The Django dependency uses an open-ended lower-bound constraint.

Several runtime dependencies have no version constraint.

Repository inspection did not identify an alternative Python dependency lock file or constraints file providing a complete resolved dependency set.

The backend Docker image installs dependencies from `requirements.txt`.

Therefore, independent builds performed at different times are not repository-evidenced as resolving the same Python dependency versions.

### Security consequence

Backend builds can resolve different dependency versions without a repository change.

A newly published transitive or direct dependency version can therefore alter application behavior, compatibility, or security characteristics between builds.

The open-ended Django constraint also permits installation of later major framework versions when compatible with package resolution.

This weakens build reproducibility, incident investigation, rollback confidence, and vulnerability remediation traceability.

This finding does not claim that an installed dependency is currently vulnerable.

It identifies the absence of a reproducible dependency resolution policy.

### Required remediation

Define a Python dependency management and locking policy.

The policy must explicitly define:

- direct dependency declaration;
- exact resolved dependency locking;
- transitive dependency capture;
- lock regeneration procedure;
- dependency update review;
- security advisory review;
- development dependency handling;
- production dependency handling;
- automated dependency update policy.

Then:

1. choose a supported dependency locking workflow;
2. separate human-maintained direct dependency declarations from the resolved lock where applicable;
3. generate a complete exact-version dependency lock;
4. make backend image builds install from the resolved dependency set;
5. commit the lock or constraints artifact to version control;
6. document the controlled lock regeneration process;
7. add dependency vulnerability review to the maintenance workflow;
8. validate dependency updates before merging.

### Required validation evidence

Remediation is not complete until evidence proves:

- two clean backend builds from the same commit resolve identical Python package versions;
- direct dependencies are explicitly declared;
- transitive dependencies are captured by the locking workflow;
- Django resolves to an intentional reviewed version;
- production image builds consume the locked dependency set;
- lock regeneration is documented and intentional;
- dependency updates produce a reviewable repository diff;
- known vulnerability review is part of the dependency update workflow;
- rollback to a previous commit restores the previous resolved dependency set;
- CI or equivalent validation detects unintended dependency drift.

---

## SEC-010 — Development database credentials and PostgreSQL host exposure are embedded in Compose

**Classification:** HARDENING  
**Severity:** P1  
**Status:** OPEN

### Evidence

`docker-compose.yml` publishes the PostgreSQL service to the host through:

`5432:5432`

The same Compose definition configures:

- `POSTGRES_DB: dental`;
- `POSTGRES_USER: dental`;
- `POSTGRES_PASSWORD: dental`.

The database credentials are therefore static and repository-known within the inspected Compose configuration.

`.env.example` also documents the Docker connection example:

`postgres://dental:dental@db:5432/dental`

`dental_clinic/settings.py` obtains the application database configuration through the environment-backed database URL.

Therefore, the Django application itself is not evidenced as hardcoding the database password in Python settings.

The inspected Compose network permits the `web` service to reach PostgreSQL through the internal service name `db`.

Repository inspection did not evidence that host publication of PostgreSQL is required for normal backend-to-database communication.

This finding does not claim that production database credentials are committed to the repository.

The observed credentials and host publication belong to the inspected development Compose configuration.

### Security consequence

The development database service is exposed on the Docker host network interface through a published PostgreSQL port.

The exposed service uses repository-known credentials.

On a workstation or deployment host where the published port is reachable by untrusted systems, the database attack surface is broader than required for communication between the backend and PostgreSQL containers.

Reusing this Compose configuration or these credentials outside an isolated development environment would create a materially unsafe database deployment.

This finding does not claim that the current PostgreSQL service is internet-accessible.

Actual network reachability depends on the Docker host, firewall, and surrounding infrastructure, which were not inspected.

### Required remediation

Define separate development and production database exposure policies.

The policy must explicitly define:

- whether PostgreSQL requires host access;
- allowed database network boundaries;
- development credential handling;
- production credential provisioning;
- credential rotation;
- database user privilege scope;
- backup access requirements;
- administrative access requirements.

Then:

1. remove PostgreSQL host port publication where host access is not required;
2. keep backend-to-database communication on the internal container network;
3. externalize database credentials from the Compose definition;
4. require explicitly provisioned database credentials;
5. prevent known development credentials from being accepted by production deployment policy;
6. define a least-privilege PostgreSQL application role;
7. separate application database credentials from administrative database credentials;
8. document controlled host access when local database administration requires it;
9. add deployment configuration validation.

### Required validation evidence

Remediation is not complete until evidence proves:

- the backend reaches PostgreSQL through the documented internal network path;
- PostgreSQL is not published to the host when host access is unnecessary;
- database credentials are explicitly provisioned outside tracked Compose configuration;
- known development credentials are rejected by production policy;
- the application uses a dedicated database role;
- the application database role has only documented required privileges;
- administrative database credentials are not used by normal application requests;
- production database credentials are absent from version control;
- database credential rotation is documented;
- development database workflows remain functional according to the documented exposure policy.

---

## SEC-011 — Transitional DRF authentication surface remains broader than the intended JWT architecture

**Classification:** HARDENING
**Severity:** P2
**Status:** OPEN

### Evidence

`dental_clinic/settings.py` defines the global DRF authentication classes as:

* `TokenAuthentication`;
* `SessionAuthentication`;
* `BasicAuthentication`.

The inspected custom login flow currently authenticates credentials and returns a DRF token to the API client.

The project maintainer has identified the current token-based authentication implementation as transitional and has stated the architectural intention to migrate the application progressively toward JWT-based authentication as the application evolves.

This declared migration intent provides context for the current authentication configuration.

However, at the audited repository state, the inspected code still uses DRF token authentication and globally enables session and basic authentication.

Repository inspection did not evidence a completed JWT authentication implementation or an authoritative authentication architecture document defining:

* the target JWT mechanism;
* access-token lifetime;
* refresh-token lifetime;
* refresh rotation;
* refresh-token revocation or blacklisting;
* logout semantics;
* password-change revocation;
* frontend credential storage;
* the migration boundary from DRF tokens to JWT.

Repository inspection also did not evidence an application requirement for globally retaining `BasicAuthentication`.

A documented React browser-session architecture requiring global `SessionAuthentication` was not identified.

This finding therefore evaluates the implemented repository state while recording the maintainer-declared JWT migration intent.

### Security consequence

The current authentication surface remains broader than the stated target architecture.

Each globally enabled authentication mechanism creates an additional credential-processing boundary that must be configured, tested, monitored, and maintained.

HTTP Basic authentication permits credentials to be presented directly through the Authorization header on supported endpoints.

Session authentication introduces cookie and CSRF security requirements distinct from token or JWT authentication.

The absence of a repository-evidenced JWT migration contract also creates a risk that authentication changes are implemented incrementally without a single authoritative credential lifecycle policy.

This finding does not evidence an authorization bypass or credential disclosure.

It identifies transitional authentication surface and an undocumented migration boundary.

### Required remediation

Treat the JWT transition as an explicit authentication architecture migration rather than an isolated authentication-class replacement.

The target policy must explicitly define:

* the selected JWT implementation;
* access-token lifetime;
* refresh-token lifetime;
* refresh-token rotation;
* refresh-token revocation or blacklisting;
* logout semantics;
* password-change revocation;
* administrator-forced revocation;
* concurrent device or session policy;
* frontend credential storage;
* frontend token renewal behavior;
* CSRF implications of the selected storage model;
* migration from existing DRF tokens;
* removal of legacy authentication mechanisms.

Then:

1. coordinate the JWT architecture with the credential lifecycle requirements of SEC-004;
2. document the target authentication contract before migration;
3. implement the selected JWT mechanism;
4. define the migration and invalidation policy for existing DRF tokens;
5. remove global `BasicAuthentication` unless an explicit documented requirement exists;
6. remove global `SessionAuthentication` unless an explicit documented browser-session requirement exists;
7. remove `TokenAuthentication` when the JWT migration boundary is complete;
8. document any temporary coexistence period and its termination criteria;
9. add authentication migration and lifecycle characterization tests.

### Required validation evidence

Remediation is not complete until evidence proves:

* the target JWT architecture is documented;
* access-token lifetime is enforced server-side;
* refresh-token lifetime is enforced according to policy;
* refresh rotation behaves according to policy;
* revoked or blacklisted refresh credentials are rejected where the selected architecture requires it;
* logout behaves according to the documented JWT policy;
* password changes invalidate credentials according to policy;
* administrator-forced revocation behaves according to policy;
* the React client stores and renews credentials according to the documented security model;
* existing DRF tokens are migrated or invalidated according to the documented transition policy;
* `BasicAuthentication` is unavailable unless explicitly required;
* `SessionAuthentication` is unavailable unless explicitly required;
* legacy `TokenAuthentication` is removed after the migration boundary is complete;
* temporary authentication coexistence does not remain indefinitely without documented justification;
* global `IsAuthenticated` protection remains effective on protected API endpoints.

---
## SEC-012 — Frontend dependency lockfiles are explicitly excluded from version control

**Classification:** HARDENING  
**Severity:** P2  
**Status:** OPEN

### Evidence

The repository root `.gitignore` explicitly ignores:

- `package-lock.json`;
- `yarn.lock`;
- `pnpm-lock.yaml`.

`frontend/package.json` defines the React frontend dependency manifest.

The declared frontend dependencies and development dependencies use compatible-version ranges, including caret constraints for:

- `react`;
- `react-dom`;
- `react-router-dom`;
- `@vitejs/plugin-react`;
- `vite`.

`frontend/Dockerfile` copies `package*.json` and executes:

`npm install`

The inspected frontend therefore uses npm while the repository explicitly prevents the npm lockfile from being tracked.

Repository inspection did not evidence an alternative committed frontend dependency lock.

As a result, the exact resolved frontend dependency tree is not repository-controlled.

### Security consequence

Frontend dependency resolution can change without a repository change.

Two installations or container builds from the same commit can resolve different direct or transitive npm package versions.

This weakens:

- build reproducibility;
- dependency vulnerability traceability;
- rollback confidence;
- software supply-chain review;
- incident investigation.

The use of compatible-version ranges increases the dependency resolver's ability to select newer package releases within the declared ranges.

This finding does not claim that an installed frontend package is currently vulnerable.

It identifies an explicitly configured loss of dependency resolution reproducibility.

### Required remediation

Define one authoritative frontend package manager and dependency locking policy.

Then:

1. select the package manager used by the project;
2. retain the corresponding lockfile in version control;
3. remove the selected lockfile from `.gitignore`;
4. keep unused package-manager lockfiles excluded where appropriate;
5. generate the lockfile from the reviewed frontend dependency manifest;
6. use deterministic dependency installation in automated and container builds;
7. replace `npm install` with `npm ci` for lockfile-controlled npm builds;
8. document controlled dependency update and lock regeneration procedures;
9. include frontend dependency vulnerability review in the maintenance workflow.

### Required validation evidence

Remediation is not complete until evidence proves:

- one authoritative frontend package manager is documented;
- the corresponding lockfile is tracked by Git;
- two clean frontend installations from the same commit resolve the same dependency tree;
- frontend container builds consume the committed lockfile;
- npm-based automated builds use `npm ci` when npm is the selected package manager;
- dependency updates produce a reviewable manifest and lockfile diff;
- transitive dependency changes are visible through the lockfile;
- known vulnerability review is part of the frontend dependency update workflow;
- rollback to a previous commit restores the previous resolved frontend dependency set;
- CI or equivalent validation detects dependency installation drift.

---



