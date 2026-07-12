import { NavLink } from 'react-router-dom'

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

function DashboardSidebar({ modules }) {
  const ordered = Array.isArray(modules)
    ? [...modules].sort((a, b) => (a?.name || '').localeCompare(b?.name || ''))
    : []

  return (
    <aside className="dashboard-sidebar">
      <h2>Navigation</h2>
      <nav className="dashboard-nav">
        <NavLink to="/dashboard" end>
          Vue d’ensemble
        </NavLink>

        {ordered.map((module) => (
          <NavLink key={module.id} to={routeForModule(module)}>
            {module.name}
          </NavLink>
        ))}
      </nav>
    </aside>
  )
}

export default DashboardSidebar
