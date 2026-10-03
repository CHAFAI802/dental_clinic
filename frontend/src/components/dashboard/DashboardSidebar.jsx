import { NavLink } from 'react-router-dom'

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

function DashboardSidebar({ modules }) {
  const { user } = useAuth()

  // Horaires de travail : accès frontend limité aux rôles autorisés sur
  // l'API /api/working-hours/ (IsAdministrator).
  const canManageWorkingHours = ['super_admin', 'administrator'].includes(user?.role)

  const ordered = Array.isArray(modules)
    ? [...modules].sort((a, b) => (a?.name || '').localeCompare(b?.name || ''))
    : []

  const links = [
    ...ordered.map((module) => ({
      key: module.id,
      to: routeForModule(module),
      label: module.name,
    })),
    ...(canManageWorkingHours
      ? [{ key: 'working-hours', to: '/dashboard/working-hours', label: 'Horaires de travail' }]
      : []),
  ].sort((a, b) => a.label.localeCompare(b.label))

  return (
    <aside className="dashboard-sidebar">
      <h2>Navigation</h2>
      <nav className="dashboard-nav">
        <NavLink to="/dashboard" end>
          Vue d’ensemble
        </NavLink>

        {links.map((link) => (
          <NavLink key={link.key} to={link.to}>
            {link.label}
          </NavLink>
        ))}
      </nav>
    </aside>
  )
}

export default DashboardSidebar
