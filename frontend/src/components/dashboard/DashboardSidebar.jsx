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

  // Paramétrage : point d’accès frontend aux pages de configuration
  // (catalogue des prestations et horaires), limité aux rôles autorisés sur
  // ces API (IsAdministrator).
  const canManageSettings = ['super_admin', 'administrator'].includes(user?.role)

  const ordered = Array.isArray(modules)
    ? [...modules].sort((a, b) => (a?.name || '').localeCompare(b?.name || ''))
    : []

  const links = [
    ...ordered.map((module) => ({
      key: module.id,
      to: routeForModule(module),
      label: module.name,
    })),
    ...(canManageSettings
      ? [{ key: 'settings', to: '/dashboard/settings', label: 'Paramétrage' }]
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
