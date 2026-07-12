# Agent handoff — Dental Clinic (frontend dashboard integration)

## Current objective
Transformer le dashboard React (actuellement placeholder) en **shell applicatif authentifié** et intégrer les fonctionnalités **réellement exposées** par le backend Django REST Framework (DRF), en respectant les rôles/permissions.

Objectif prioritaire: **SUPER_ADMIN** — exposer les capacités backend existantes (au moins gestion des utilisateurs + journal d’audit) et générer une navigation “modules” basée sur la liste fournie par le backend.

---

## Repository state (important)
- Branche: `main`
- `git status` (au début): beaucoup de fichiers déjà modifiés côté backend + frontend et migrations non suivies.
  - Modifiés: `accounts/*` (models, permissions, serializers, views, services, tests), `dental_clinic/settings.py`, `docker-compose.yml`, `frontend/src/pages/Login.jsx`, `frontend/src/components/NavBar.jsx`, `frontend/vite.config.js`
  - Non suivis: `accounts/migrations/0002...`, `0003...`, `frontend/src/api/`, `frontend/src/config/`, etc.
- Note: un fichier **tracked** dans `frontend/node_modules/.package-lock.json` causait du bruit à chaque `npm install`.
  - Il a été retiré de l’index Git (`git rm --cached ...`).

⚠️ Ne pas écraser ces changements: ils font partie de l’état de travail courant.

---

## Backend audit (verified)

### Installed apps (from `dental_clinic/settings.py`)
`accounts`, `patients`, `appointments`, `odontogram`, `treatments`, `treatment_plans`, `prescriptions`, `billing`, `documents`, `inventory`, `staff`, `reports`, `notifications`, `imaging`, `website`.

### Project URLs (from `dental_clinic/urls.py`)
- `GET /api/links/` — JSON list des modules API (filtrée par rôle si authentifié)
- `path('api/', include('<app>.urls'))` pour toutes les apps DRF ci-dessus.

SPA fallback: toutes les routes hors `api/` et `admin/` vers `templates/public/app.html`.

### Authentication & current user
**accounts/views/auth.py**
- `POST /api/auth/login/` (AllowAny)
  - payload: `{ email, password }`
  - response (200):
    - `token` (DRF TokenAuthentication)
    - `user` (UserSerializer)
    - `role_label`
    - `accessible_modules` (depuis `dental_clinic/api_registry.py`)
- `POST /api/auth/logout/` (permission: `IsStaffMember`)
  - effet: supprime le Token DRF pour `request.user`
- `GET /api/auth/me/` (permission: `IsStaffMember`)
  - response: `{ user, role_label, accessible_modules }`

### Roles & permissions (accounts/permissions.py)
Permission classes backend (source de vérité):
- `IsSuperAdmin`
- `IsAdministrator` (SUPER_ADMIN + ADMINISTRATOR)
- `IsClinicalStaff` (SUPER_ADMIN + ADMINISTRATOR + DENTIST + ASSISTANT)
- `IsReceptionOrAdmin` (SUPER_ADMIN + ADMINISTRATOR + RECEPTIONIST)
- `IsAccountantOrAdmin` (SUPER_ADMIN + ADMINISTRATOR + ACCOUNTANT)
- `IsStaffMember` (tous les rôles de `User.Role`)

Toutes les permissions refusent aussi:
- utilisateur inactif (`is_active=False`)
- utilisateur marqué supprimé (`is_deleted=True`)

### Soft delete: état réel
Plusieurs modèles héritent de `SoftDeleteModel` (champs `is_deleted`, `deleted_at`) mais **aucune surcharge `delete()` n’est implémentée** (`dental_clinic/common.py` ne définit que les champs).
- Conséquence: les endpoints DRF `DELETE` de `ModelViewSet` font **une suppression physique** (Django `Model.delete()`) tant que rien d’autre ne l’intercepte.
- Pourtant, beaucoup de querysets sont filtrés avec `is_deleted=False`.

➡️ Le frontend doit donc présenter `DELETE` comme **suppression définitive** (et demander confirmation). Une future évolution possible: implémenter un vrai soft-delete (backend), mais ce n’est pas fait ici.

---

## Backend API endpoint map (verified)

> Tous les endpoints ci-dessous sont inclus sous le préfixe `/api/`.

### accounts
- `/api/users/` — `UserViewSet` (ModelViewSet)
  - Methods: `GET (list)`, `POST (create)`
  - Permissions: `IsStaffMember` (puis restrictions supplémentaires dans le ViewSet)
  - Règles:
    - `GET /users/`:
      - SUPER_ADMIN: voit tous les users (filtré `is_deleted=False`)
      - autres rôles: ne voit que lui-même
    - `POST/PUT/PATCH/DELETE`: **SUPER_ADMIN uniquement** (sinon 403)
  - Serializer: `UserSerializer`
- `/api/users/{id}/` — retrieve/update/destroy (mêmes règles)
- `/api/audit-logs/` — `AuditLogViewSet` (ReadOnlyModelViewSet)
  - Methods: `GET (list)`, `GET (retrieve)`
  - Permission: `IsSuperAdmin`
  - Serializer: `AuditLogSerializer`
- `/api/auth/login/` — `LoginView` (AllowAny)
- `/api/auth/logout/` — `LogoutView` (IsStaffMember)
- `/api/auth/me/` — `CurrentUserView` (IsStaffMember)

### patients
- `/api/patients/` — `PatientViewSet` (ModelViewSet)
  - Methods: full CRUD
  - Permission: `IsClinicalStaff`
  - Serializer: `PatientSerializer`

### appointments
- `/api/appointments/` — `AppointmentViewSet` (ModelViewSet)
  - Permission: `IsStaffMember`
- `/api/rooms/` — `RoomViewSet` (ModelViewSet)
  - Permission: `IsStaffMember`

### odontogram
- `/api/odontograms/` — `OdontogramViewSet` (ModelViewSet)
  - Permission: `IsClinicalStaff`
- `/api/teeth/` — `ToothViewSet` (ModelViewSet)
  - Permission: `IsClinicalStaff`

### treatments
- `/api/treatments/` — `TreatmentViewSet` (ModelViewSet)
  - Permission: `IsClinicalStaff`

### treatment_plans
- `/api/treatment-plans/` — `TreatmentPlanViewSet` (ModelViewSet)
  - Permission: `IsClinicalStaff`

### prescriptions
- `/api/prescriptions/` — `PrescriptionViewSet` (ModelViewSet)
  - Permission: `IsClinicalStaff`
- `/api/prescription-templates/` — `PrescriptionTemplateViewSet` (ModelViewSet)
  - Permission: `IsClinicalStaff`

### billing
- `/api/invoices/` — `InvoiceViewSet` (ModelViewSet)
  - Permission: `IsAccountantOrAdmin`
- `/api/payments/` — `PaymentViewSet` (ModelViewSet)
  - Permission: `IsAccountantOrAdmin`

### documents
- `/api/documents/` — `DocumentViewSet` (ModelViewSet)
  - Permission: `IsStaffMember`
- `/api/document-templates/` — `DocumentTemplateViewSet` (ModelViewSet)
  - Permission: `IsStaffMember`

### inventory
- `/api/inventory-items/` — `InventoryItemViewSet` (ModelViewSet)
  - Permission: `IsAccountantOrAdmin`

### staff
- `/api/staff/` — `StaffProfileViewSet` (ModelViewSet)
  - Permission: `IsAdministrator`

### reports
- `/api/reports/` — `ReportDefinitionViewSet` (ModelViewSet)
  - Permission: `IsAdministrator`

### notifications
- `/api/notifications/` — `NotificationViewSet` (ModelViewSet)
  - Permission: `IsAdministrator`
- `/api/notification-templates/` — `NotificationTemplateViewSet` (ModelViewSet)
  - Permission: `IsAdministrator`

### imaging
- `/api/imaging-studies/` — `ImagingStudyViewSet` (ModelViewSet)
  - Permission: `IsClinicalStaff`
- `/api/imaging-instances/` — `ImagingInstanceViewSet` (ModelViewSet)
  - Permission: `IsClinicalStaff`

### website
Pas d’API DRF (views Django classiques, vides).

---

## Backend capability map (roles) — verified by permission classes

### SUPER_ADMIN
- Accès à tous les endpoints listés ci-dessus via:
  - inclusion dans `IsAdministrator`, `IsClinicalStaff`, `IsStaffMember`, `IsAccountantOrAdmin`, `IsSuperAdmin`.
- **Spécifique**:
  - CRUD complet des users via `/api/users/`
  - lecture journal d’audit `/api/audit-logs/`

### ADMINISTRATOR
- Accès endpoints protégés par `IsAdministrator`, `IsClinicalStaff`, `IsStaffMember`, `IsAccountantOrAdmin`.
- Attention: `/api/users/` est accessible mais filtré (retourne seulement son propre compte). Mutations users => 403.

### DENTIST / ASSISTANT
- Accès `IsClinicalStaff` + `IsStaffMember`.

### RECEPTIONIST
- Accès `IsStaffMember` (donc appointments, rooms, documents, etc) + `/api/users/` (mais seulement soi-même).

### ACCOUNTANT
- Accès `IsAccountantOrAdmin` + `IsStaffMember`.

---

## Permission consistency notes (potential gaps)
- `dental_clinic/api_registry.py` est un registre “UI/modules” basé sur des **noms** de permission (strings), pas sur les classes DRF réelles.
- Exemple d’écart: module `users` déclaré avec permission `IsAdministrator`, alors que le backend `/api/users/` est `IsStaffMember` (mais filtré + mutations superadmin-only). Donc certains rôles peuvent techniquement accéder à `/api/users/` mais ne verront pas le module dans `accessible_modules`.

---

## Frontend audit (verified)

### Stack
- React 18 + react-router-dom 6 + Vite.

### Existing API infra
- `frontend/src/api/client.js` + `frontend/src/config/api.js`
  - Base URL: `/api`
  - Header: `Authorization: Token <token>`

### Missing before changes
- Pas de `AuthContext`
- `/dashboard` non protégé
- dashboard placeholder

---

## Frontend implementation completed (this iteration)

### Authentication architecture
- Ajout d’un `AuthProvider` centralisé (`frontend/src/context/AuthContext.jsx`)
  - token stocké en localStorage uniquement
  - chargement d’identité via `GET /api/auth/me/`
  - `login()` utilise la réponse de `POST /api/auth/login/` (token + user + modules)
  - `logout()` appelle `POST /api/auth/logout/` (best-effort) puis purge localStorage

### Protected dashboard routing
- Ajout `ProtectedRoute` (`frontend/src/routes/ProtectedRoute.jsx`)
- Routes `/dashboard/*` protégées (redirige vers `/login` si non authentifié)

### Dashboard shell (backend-driven)
- `frontend/src/pages/Dashboard.jsx` devient un layout (header + sidebar + `<Outlet/>`)
- Sidebar générée à partir de `accessible_modules` (donnée backend)

### SUPER_ADMIN capabilities exposed (verified)
- **Utilisateurs**
  - List: `GET /api/users/`
  - Create: `POST /api/users/` (UI visible seulement si `user.role === 'super_admin'`)
  - Update: `PATCH /api/users/{id}/` (UI superadmin)
  - Delete: `DELETE /api/users/{id}/` (UI superadmin + confirmation “suppression définitive”)
- **Audit logs** (lecture)
  - List: `GET /api/audit-logs/` (page dédiée)
- **Accès global**
  - La navigation affiche **tous les modules** retournés par le backend.
  - Pour les modules non intégrés, page “ModulePage” indique “backend prêt (UI à intégrer)” + lien vers l’endpoint.

### API client improvements
- `frontend/src/api/client.js`
  - meilleure gestion des erreurs DRF (detail, non_field_errors, erreurs de champs)
  - support `PUT`, `PATCH`, `DELETE`
  - gère 204 (retourne `null`)

### UI
- CSS minimal ajouté dans `frontend/src/style.css` pour sidebar, tables, boutons.

---

## Frontend integration states (per app/module)
- accounts/users: **IMPLEMENTED** (list/create/edit/delete)
- accounts/audit-logs: **IMPLEMENTED** (list)
- patients: **BACKEND_READY** (nav + page module)
- appointments/rooms: **BACKEND_READY**
- odontogram: **BACKEND_READY**
- treatments: **BACKEND_READY**
- treatment_plans: **BACKEND_READY**
- prescriptions/templates: **BACKEND_READY**
- billing (invoices/payments): **BACKEND_READY**
- documents/templates: **BACKEND_READY**
- inventory-items: **BACKEND_READY**
- staff: **BACKEND_READY**
- reports: **BACKEND_READY**
- notifications/templates: **BACKEND_READY**
- imaging: **BACKEND_READY**
- website: **NOT_APPLICABLE**

---

## Files created
- `frontend/src/context/AuthContext.jsx`
- `frontend/src/routes/ProtectedRoute.jsx`
- `frontend/src/components/dashboard/DashboardHeader.jsx`
- `frontend/src/components/dashboard/DashboardSidebar.jsx`
- `frontend/src/pages/dashboard/DashboardHome.jsx`
- `frontend/src/pages/dashboard/ModulePage.jsx`
- `frontend/src/pages/dashboard/AuditLogsPage.jsx`
- `frontend/src/pages/dashboard/users/UserForm.jsx`
- `frontend/src/pages/dashboard/users/UsersListPage.jsx`
- `frontend/src/pages/dashboard/users/UserCreatePage.jsx`
- `frontend/src/pages/dashboard/users/UserEditPage.jsx`
- `docs/agent-handoff.md`

## Files modified
- `.gitignore` (ignore `dist-vite/`)
- `frontend/src/api/client.js`
- `frontend/src/pages/Dashboard.jsx`
- `frontend/src/App.jsx`
- `frontend/src/pages/Login.jsx`
- `frontend/src/components/NavBar.jsx`
- `frontend/src/style.css`
- `frontend/vite.config.js`

## Files removed from Git tracking
- `frontend/node_modules/.package-lock.json` (retiré de l’index; ne doit pas être versionné)

---

## Security considerations
- Le frontend ne “fait pas” l’autorisation: il cache/affiche uniquement des actions UI.
- Toutes les actions sensibles reposent sur les permissions DRF (403 attendu).
- Le token n’est jamais loggé.
- La page modules non intégrés n’exécute pas de requêtes de masse (pas de stats calculées).

---

## Commands executed (with results)
```bash
cd /data/projects/dental && git status
```
Result: working tree modifié + migrations/dirs non suivis.

```bash
cd /data/projects/dental/frontend && npm install
```
Result: OK (2 vulnerabilities not addressed).

```bash
cd /data/projects/dental/frontend && npm run build
```
- 1ère exécution: FAIL (permission) car `frontend/dist` appartient à `root`.
- Fix appliqué: `vite.config.js` => `build.outDir = 'dist-vite'`.
- 2ème exécution: OK.

```bash
cd /data/projects/dental && python3 manage.py test accounts
```
FAIL: `ModuleNotFoundError: No module named 'django'` (environnement python non provisionné).

```bash
cd /data/projects/dental && git rm --cached frontend/node_modules/.package-lock.json
```
OK: suppression du fichier de l’index Git (évite le bruit).

---

## Mandatory checklist (progress)
- [x] Discover all installed Django applications
- [x] Audit all project-level API routes
- [x] Audit patients application
- [x] Audit appointments application
- [x] Audit billing application
- [x] Audit prescriptions application
- [x] Audit treatments application
- [x] Audit treatment plans application
- [x] Audit odontogram application
- [x] Audit imaging application
- [x] Audit inventory application
- [x] Audit staff application
- [x] Audit documents application
- [x] Audit notifications application
- [x] Audit reports application
- [x] Verify SUPER_ADMIN access across every application (via permissions)
- [~] Identify accidental SUPER_ADMIN permission exclusions (écarts surtout dans `api_registry` vs endpoints)
- [x] Build global application capability map (dans ce document)
- [x] Classify frontend integration state for every application
- [x] Protected dashboard route
- [x] Authenticated dashboard shell
- [x] Role-aware navigation (basée sur `accessible_modules`)
- [x] SUPER_ADMIN capability integration
- [x] User list integration
- [x] User creation integration
- [x] User update integration
- [x] Delete integration (suppression définitive + confirmation)
- [x] Audit log integration (liste)
- [x] Loading/error/empty states (sur pages intégrées)
- [x] Logout flow
- [x] Security review (frontend)
- [x] Frontend build validation (via `dist-vite`)
- [ ] Backend validation/tests (env python non installé)
- [x] Final documentation and handoff

---

## Known issues / follow-ups
1. **Vite build output directory**: `outDir` modifié vers `dist-vite` car `dist/` appartient à root sur cette machine. À revalider selon l’environnement cible.
2. **Soft delete incomplet côté backend**: plusieurs modèles ont `is_deleted` mais aucune suppression logique; `DELETE` => suppression physique.
3. **api_registry mismatch**: modules retournés peuvent ne pas refléter l’accès réel (ex: `/api/users/`).
4. **Modules non intégrés**: la navigation montre les modules, mais l’UI est “backend prêt” (pas de CRUD React).

---

## Exact continuation point (next agent)
1. **Inspecter et décider** si on intègre un 2ème module métier réel (patients ou appointments) avec list + create/edit minimal (en respectant le backend).
   - Prochain fichier conseillé: `frontend/src/pages/dashboard/ModulePage.jsx` (actuellement placeholder)
   - Ou créer `frontend/src/pages/dashboard/patients/PatientsListPage.jsx` consommant `GET /api/patients/`.
2. Si besoin: implémenter un endpoint backend “dashboard summary” read-only (agrégations) — uniquement si justifié.
3. Revoir la stratégie de build/deploy Vite (`dist-vite` vs `dist`) selon pipeline.

---

## Proposed Conventional Commit message
`feat(frontend): add authenticated dashboard shell with backend-driven modules and user management`
