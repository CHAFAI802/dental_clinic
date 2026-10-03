import { useEffect, useState } from 'react'
import { Link, NavLink, useLocation, useNavigate } from 'react-router-dom'

import { useAuth } from '../context/AuthContext.jsx'
import { useSiteConfig } from '../context/SiteConfigContext.jsx'
import Icon from './common/Icon.jsx'
import Logo from './logo.jsx'

/**
 * Navigation principale :
 * - liens, libellés et bouton de prise de rendez-vous → siteConfig.nav ;
 * - authentification → AuthContext existant (inchangé) ;
 * - menu responsive (burger) fermé à chaque changement de route.
 */
function NavBar() {
  const navigate = useNavigate()
  const location = useLocation()
  const { isAuthenticated, logout } = useAuth()
  const { config } = useSiteConfig()

  const { links, cta, showLogin, loginLabel, dashboardLabel, logoutLabel } = config.nav
  const [isMenuOpen, setIsMenuOpen] = useState(false)

  useEffect(() => {
    setIsMenuOpen(false)
  }, [location.pathname])

  const handleLogout = async () => {
    await logout()
    navigate('/', { replace: true })
  }

  return (
    <header className="nav-bar">
      <Logo />

      <button
        type="button"
        className="nav-toggle"
        aria-expanded={isMenuOpen}
        aria-controls="primary-navigation"
        aria-label={isMenuOpen ? 'Fermer le menu' : 'Ouvrir le menu'}
        onClick={() => setIsMenuOpen((open) => !open)}
      >
        <Icon name={isMenuOpen ? 'close' : 'menu'} />
      </button>

      <nav
        id="primary-navigation"
        className={`nav-links${isMenuOpen ? ' open' : ''}`}
        aria-label="Navigation principale"
      >
        {links.map((link) => (
          <NavLink key={link.to} to={link.to} end={link.to === '/'}>
            {link.label}
          </NavLink>
        ))}

        {cta?.label && (
          <Link className="btn btn-accent" to={cta.to || '/contact'}>
            {cta.label}
          </Link>
        )}

        {isAuthenticated ? (
          <>
            <NavLink to="/dashboard">{dashboardLabel}</NavLink>
            <button type="button" className="nav-link-button" onClick={handleLogout}>
              {logoutLabel}
            </button>
          </>
        ) : (
          showLogin && <NavLink to="/login">{loginLabel}</NavLink>
        )}
      </nav>
    </header>
  )
}

export default NavBar
