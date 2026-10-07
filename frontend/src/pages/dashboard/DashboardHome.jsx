import { Link } from 'react-router-dom'
import { useAuth } from '../../context/AuthContext.jsx'

function routeForModule(module) {
  if (!module?.id) return '/dashboard'

  switch (module.id) {
    case 'users':
      return '/dashboard/users'
    case 'audit-logs':
      return '/dashboard/audit-logs'
    default:
      return `/dashboard/modules/${module.id}`
  }
}

function ModuleIcon({ moduleId }) {
  const commonProps = {
    width: 42,
    height: 42,
    viewBox: '0 0 24 24',
    fill: 'none',
    stroke: 'currentColor',
    strokeWidth: 1.8,
    strokeLinecap: 'round',
    strokeLinejoin: 'round',
    'aria-hidden': true,
  }

  switch (moduleId) {
    case 'users':
      return (
        <svg {...commonProps}>
          <path d="M16 21v-2a4 4 0 0 0-4-4H6a4 4 0 0 0-4 4v2" />
          <circle cx="9" cy="7" r="4" />
          <path d="M22 21v-2a4 4 0 0 0-3-3.87" />
          <path d="M16 3.13a4 4 0 0 1 0 7.75" />
        </svg>
      )

    case 'audit-logs':
      return (
        <svg {...commonProps}>
          <path d="M4 4h16v16H4z" />
          <path d="M8 8h8" />
          <path d="M8 12h8" />
          <path d="M8 16h5" />
        </svg>
      )

    case 'patients':
      return (
        <svg {...commonProps}>
          <circle cx="9" cy="7" r="4" />
          <path d="M2 21a7 7 0 0 1 14 0" />
          <path d="M19 8v6" />
          <path d="M16 11h6" />
        </svg>
      )

    case 'appointments':
      return (
        <svg {...commonProps}>
          <rect x="3" y="4" width="18" height="17" rx="2" />
          <path d="M16 2v4M8 2v4M3 10h18" />
          <path d="M8 14h.01M12 14h.01M16 14h.01M8 18h.01M12 18h.01" />
        </svg>
      )

    case 'rooms':
      return (
        <svg {...commonProps}>
          <path d="M3 21V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2v16" />
          <path d="M3 21h18" />
          <path d="M8 7h8v5H8z" />
          <path d="M8 16h3M14 16h2" />
        </svg>
      )

    case 'odontograms':
      return (
        <svg {...commonProps}>
          <path d="M8 3c-2 0-4 2-4 5 0 5 2 13 5 13 2 0 2-4 3-4s1 4 3 4c3 0 5-8 5-13 0-3-2-5-4-5-2 0-3 1-4 1S10 3 8 3z" />
        </svg>
      )

    case 'dentists':
    case 'staff':
      return (
        <svg {...commonProps}>
          <circle cx="12" cy="7" r="4" />
          <path d="M5 21a7 7 0 0 1 14 0" />
          <path d="M19 8l2 2-2 2" />
        </svg>
      )

    case 'treatments':
      return (
        <svg {...commonProps}>
          <path d="M6 3h12v4H6z" />
          <path d="M8 7v14M16 7v14" />
          <path d="M5 21h14" />
          <path d="M10 11h4M10 15h4" />
        </svg>
      )

    case 'treatment-plans':
      return (
        <svg {...commonProps}>
          <path d="M5 3h14v18H5z" />
          <path d="M8 7h8M8 11h8M8 15h5" />
          <path d="M8 19h8" />
        </svg>
      )

    case 'prescriptions':
      return (
        <svg {...commonProps}>
          <path d="M7 3h10a2 2 0 0 1 2 2v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2z" />
          <path d="M9 8h6M9 12h6M9 16h4" />
        </svg>
      )

    case 'prescription-templates':
      return (
        <svg {...commonProps}>
          <path d="M4 4h16v16H4z" />
          <path d="M8 8h8M8 12h8M8 16h5" />
        </svg>
      )

    case 'invoices':
    case 'payments':
      return (
        <svg {...commonProps}>
          <rect x="3" y="5" width="18" height="14" rx="2" />
          <path d="M3 10h18" />
          <path d="M8 15h4" />
        </svg>
      )

    case 'documents':
    case 'document-templates':
      return (
        <svg {...commonProps}>
          <path d="M6 2h9l4 4v16H6z" />
          <path d="M15 2v5h4M9 12h6M9 16h6" />
        </svg>
      )

    case 'inventory-items':
      return (
        <svg {...commonProps}>
          <path d="M3 7l9-4 9 4-9 4z" />
          <path d="M3 7v10l9 4 9-4V7" />
          <path d="M12 11v10" />
        </svg>
      )

    case 'settings':
      return (
        <svg {...commonProps}>
          <circle cx="12" cy="12" r="3" />
          <path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 1 1-2.83 2.83l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-4 0v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 1 1-2.83-2.83l.06-.06a1.65 1.65 0 0 0 .33-1.82 1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1 0-4h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 1 1 2.83-2.83l.06.06a1.65 1.65 0 0 0 1.82.33H9a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 4 0v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 1 1 2.83 2.83l-.06.06a1.65 1.65 0 0 0-.33 1.82V9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 0 4h-.09a1.65 1.65 0 0 0-1.51 1z" />
        </svg>
      )

    case 'reports':
      return (
        <svg {...commonProps}>
          <path d="M4 19V5M4 19h17" />
          <path d="M8 16v-5M12 16V7M16 16v-8M20 16v-4" />
        </svg>
      )

    case 'notifications':
    case 'notification-templates':
      return (
        <svg {...commonProps}>
          <path d="M18 8a6 6 0 0 0-12 0c0 7-3 7-3 9h18c0-2-3-2-3-9" />
          <path d="M10 21h4" />
        </svg>
      )

    case 'imaging-studies':
    case 'imaging-instances':
      return (
        <svg {...commonProps}>
          <rect x="3" y="3" width="18" height="18" rx="2" />
          <circle cx="12" cy="12" r="4" />
          <path d="M12 8v8M8 12h8" />
        </svg>
      )

    default:
      return (
        <svg {...commonProps}>
          <rect x="4" y="4" width="6" height="6" rx="1" />
          <rect x="14" y="4" width="6" height="6" rx="1" />
          <rect x="4" y="14" width="6" height="6" rx="1" />
          <rect x="14" y="14" width="6" height="6" rx="1" />
        </svg>
      )
  }
}

function DashboardHome() {
  const { accessibleModules, user } = useAuth()

  // Paramétrage : entrée frontend dédiée, visible uniquement pour les rôles
  // autorisés sur les API concernées (IsAdministrator). Elle ne dépend pas
  // d'un éventuel module « settings » retourné par le backend.
  const canManageSettings = ['super_admin', 'administrator'].includes(user?.role)

  const modules = Array.isArray(accessibleModules) ? accessibleModules : []

  if (modules.length === 0 && !canManageSettings) {
    return (
      <section>
        <h2>Vue d’ensemble</h2>
        <p>Aucun module accessible n’a été retourné par le backend.</p>
      </section>
    )
  }

  return (
    <section>
      <h2>Vue d’ensemble</h2>
      <p>Modules accessibles.</p>

      <div className="dashboard-grid">
        {modules.map((module) => (
          <Link
            key={module.id}
            to={routeForModule(module)}
            className="dashboard-card dashboard-module-card"
          >
            <div className="dashboard-module-icon">
              <ModuleIcon moduleId={module.id} />
            </div>

            <h3>{module.name}</h3>

            <p className="dashboard-card-desc">
              {module.description}
            </p>
          </Link>
        ))}

        {canManageSettings && (
          <Link
            to="/dashboard/settings"
            className="dashboard-card dashboard-module-card"
          >
            <div className="dashboard-module-icon">
              <ModuleIcon moduleId="settings" />
            </div>

            <h3>Paramétrage</h3>

            <p className="dashboard-card-desc">
              Catégories de prestations, prestations, tarifs et horaires de travail.
            </p>
          </Link>
        )}
      </div>
    </section>
  )
}

export default DashboardHome