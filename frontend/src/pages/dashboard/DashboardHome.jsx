import { Link } from 'react-router-dom'

import { useAuth } from '../../context/AuthContext.jsx'

const IMPLEMENTED_MODULE_IDS = new Set(['users', 'audit-logs'])

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

function DashboardHome() {
  const { accessibleModules } = useAuth()

  if (!Array.isArray(accessibleModules) || accessibleModules.length === 0) {
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
      <p>Modules accessibles (source: backend).</p>

      <div className="dashboard-grid">
        {accessibleModules.map((module) => {
          const status = IMPLEMENTED_MODULE_IDS.has(module.id) ? 'Implémenté' : 'Backend prêt (UI à intégrer)'
          return (
            <article key={module.id} className="dashboard-card">
              <h3>
                <Link to={routeForModule(module)}>{module.name}</Link>
              </h3>
              <p className="dashboard-card-desc">{module.description}</p>
              <p className="dashboard-card-meta">
                <strong>API</strong> : <code>{module.path}</code>
              </p>
              <p className="dashboard-card-meta">
                <strong>Statut</strong> : {status}
              </p>
            </article>
          )
        })}
      </div>
    </section>
  )
}

export default DashboardHome
