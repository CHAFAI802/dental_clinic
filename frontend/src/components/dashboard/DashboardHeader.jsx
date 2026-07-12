import { useNavigate } from 'react-router-dom'

import { useAuth } from '../../context/AuthContext.jsx'

function DashboardHeader() {
  const navigate = useNavigate()
  const { user, roleLabel, logout } = useAuth()

  const handleLogout = async () => {
    await logout()
    navigate('/', { replace: true })
  }

  return (
    <header className="dashboard-header">
      <div>
        <h1>Dashboard</h1>
        {user && (
          <p className="dashboard-user">
            Connecté en tant que <strong>{user.first_name} {user.last_name}</strong> ({roleLabel || user.role})
          </p>
        )}
      </div>

      <button type="button" className="dashboard-logout" onClick={handleLogout}>
        Déconnexion
      </button>
    </header>
  )
}

export default DashboardHeader
