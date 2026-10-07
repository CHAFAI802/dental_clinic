import { NavLink, Outlet } from 'react-router-dom'

import { useAuth } from '../../../context/AuthContext.jsx'

/*
 * Conteneur du Paramétrage (entrée frontend dédiée du dashboard).
 *
 * Sections mappées sur les endpoints réellement déclarés par le backend :
 * - /api/prestation-categories/ → PrestationCategoryViewSet (IsAdministrator)
 * - /api/prestations/           → PrestationViewSet (IsAdministrator)
 * - /api/prestation-tarifs/     → PrestationTarifViewSet (IsAdministrator)
 * - /api/working-hours/         → page existante /dashboard/working-hours
 *
 * Les trois premières sections réutilisent les pages déjà présentes dans le
 * module Billing (aucune duplication de logique, aucune nouvelle API).
 * « Horaires de travail » navigue vers la page existante, non dupliquée.
 *
 * Le backend reste l'autorité de sécurité : cette règle sert uniquement à
 * refuser l'accès frontend (convention des pages existantes, cf.
 * WorkingHoursPage / UserCreatePage).
 */
const SECTIONS = [
  {
    id: 'prestation-categories',
    label: 'Catégories de prestations',
    to: '/dashboard/settings/prestation-categories',
  },
  {
    id: 'prestations',
    label: 'Prestations',
    to: '/dashboard/settings/prestations',
  },
  {
    id: 'prestation-tarifs',
    label: 'Tarifs des prestations',
    to: '/dashboard/settings/prestation-tarifs',
  },
  {
    id: 'working-hours',
    label: 'Horaires de travail',
    to: '/dashboard/working-hours',
  },
]

function SettingsPage() {
  const { user: currentUser } = useAuth()

  const canManageSettings = ['super_admin', 'administrator'].includes(currentUser?.role)

  if (!canManageSettings) {
    return (
      <section>
        <h2>Paramétrage</h2>
        <p className="error-text">
          Accès refusé. Seuls le super admin et les administrateurs peuvent accéder au
          paramétrage.
        </p>
      </section>
    )
  }

  return (
    <div>
      <nav
        className="dashboard-nav"
        aria-label="Navigation paramétrage"
        style={{
          display: 'flex',
          flexWrap: 'wrap',
          gap: 'var(--space-2)',
          marginBottom: 'var(--space-4)',
        }}
      >
        {SECTIONS.map((section) => (
          <NavLink key={section.id} to={section.to}>
            {section.label}
          </NavLink>
        ))}
      </nav>

      <Outlet />
    </div>
  )
}

export default SettingsPage
