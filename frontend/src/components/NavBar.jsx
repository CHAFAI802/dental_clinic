import { NavLink, useNavigate } from 'react-router-dom'

import { useAuth } from '../context/AuthContext.jsx'

function NavBar() {
  const navigate = useNavigate()
  const { isAuthenticated, logout } = useAuth()

  const handleLogout = async () => {
    await logout()
    navigate('/', { replace: true })
  }

  return (
    <header className="nav-bar">
      <nav>
        <NavLink to="/" end>
          Accueil
        </NavLink>
        <NavLink to="/services">Services</NavLink>
        <NavLink to="/team">Équipe</NavLink>
        <NavLink to="/team/profile">Profile</NavLink>
        <NavLink to="/contact">Contact</NavLink>
        
        {isAuthenticated ? (
          <>
            <NavLink to="/dashboard">Dashboard</NavLink>
            <button type="button" className="nav-link-button" onClick={handleLogout}>
              Déconnexion
            </button>
          </>
        ) : (
          <NavLink to="/login">Connexion</NavLink>
        )}
      </nav>
    </header>
  )
}

export default NavBar
