# WEBSITE DOMAIN SPECIFICATION

## Scope

PHASE B11 characterizes the current `website` application and the public website delivery architecture.

This phase documents the implementation that currently exists.

No website domain models, CMS behavior, public API, or routing remediation is implemented in this phase.

---

## Current application state

The `website` Django application is installed in `INSTALLED_APPS`.

The application currently contains:

- `website/apps.py`
- `website/models.py`
- `website/views.py`
- `website/admin.py`
- `website/tests.py`

The application does not currently implement a website business domain.

---

## Domain model inventory

Runtime Django application metadata reports zero concrete models for the `website` application.

`website/models.py` defines no Django model classes.

There are currently no persistent website-domain entities for:

- site settings
- clinic identity
- services
- team members
- doctor profiles
- public contact information
- opening hours
- public content
- navigation
- homepage content

Therefore the current public website content is not backed by a dedicated Django domain model.

---

## Serializer and API surface

The `website` application has no serializer module.

No website-specific DRF serializer was identified.

No website-specific ViewSet or API view was identified.

No `website.urls` URL configuration is currently included in the project router.

Therefore there is no dedicated backend API contract for public website content.

---

## Public delivery architecture

The project-level URL configuration defines a SPA catch-all route.

The catch-all excludes:

- `/api/`
- `/admin/`
- `/static/`
- `/media/`
- `favicon.ico`
- `robots.txt`

All other routes are served through:

`public/app.html`

The template contains the React mount point:

`<div id="react-root"></div>`

The current public application architecture is therefore SPA-oriented.

Django acts as the shell delivery layer while client-side routing and rendering are expected to own the public application surface.

---

## Legacy Django template residue

The repository still contains:

- `templates/public/base_public.html`
- `templates/public/partials/navbar.html`
- `templates/public/partials/footer.html`

These templates contain historical Django URL references including:

- `home`
- `services`
- `team`
- `contact`
- `login`
- `dashboard`

The current project URL configuration does not define these named Django routes.

This template structure represents architectural residue from the previous server-rendered public website implementation.

It does not define the current public routing contract.

---

## Static clinic content

Legacy public templates contain hard-coded clinic identity and contact content.

Examples include:

- `Cabinet Dentaire ELQODS`
- `Dr CHAFAI Alaa Eddine`
- `Sétif`
- `contact@elqods.dz`
- placeholder telephone content

The base public template also contains hard-coded SEO metadata describing dental services.

This information is not currently represented by website-domain models or a public website API.

---

## Current domain guarantees

The current implementation guarantees only that:

1. the `website` Django application is installed;
2. the application defines zero concrete domain models;
3. no dedicated website URL configuration is exposed;
4. the public surface is delivered through the project SPA catch-all;
5. `public/app.html` is the SPA shell template.

No backend guarantee currently exists for persistence or API delivery of public website content.

---

## Architectural interpretation

The `website` application is currently a placeholder application.

It does not own the public website domain.

The effective public architecture is:

`Django catch-all route -> public/app.html -> React mount point -> client-side application`

Website content ownership is therefore currently frontend-oriented and static rather than backend-domain-driven.

---

## Identified gaps

The current implementation has the following domain gaps:

- no website-domain models;
- no persisted site settings;
- no persisted clinic profile;
- no persisted services catalog;
- no persisted public team catalog;
- no public website serializer contract;
- no public website API;
- no backend content publication workflow;
- no explicit website-domain ownership boundary;
- legacy Django template routing references remain in the repository.

These are characterization findings, not PHASE B11 remediation tasks.

---

## Recommended future domain boundary

If public website content is intended to become administratively managed, the `website` application should become the owner of that domain.

Potential future entities may include:

- `SiteSettings`
- `ClinicProfile`
- `PublicService`
- `PublicTeamMember`
- `OpeningHours`
- `ContactInformation`

The exact model design must be driven by confirmed product requirements.

PHASE B11 does not introduce these models.

---

## Test coverage

Executable characterization coverage is provided by:

`accounts/tests/test_website_domain_audit.py`

The tests verify:

- `website` is installed;
- the application has zero concrete domain models;
- `website.models` defines no Django models;
- no website-specific URL configuration is exposed;
- the public surface uses the SPA catch-all and `public/app.html`.

---

## Conclusion

The current `website` application does not implement a backend website domain.

The public application is delivered as a React-oriented SPA shell through Django's catch-all route.

Legacy server-rendered public templates remain in the repository and reference named routes that are not part of the current Django URL contract.

A future website-domain implementation requires an explicit product decision about whether public content remains frontend-static or becomes backend-managed.

Remediation and architectural implementation are deferred to PHASE B13.
