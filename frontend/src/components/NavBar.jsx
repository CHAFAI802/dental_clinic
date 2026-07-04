import { NavLink } from 'react-router-dom'

function NavBar() {
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
        <NavLink to="/login">Connexion</NavLink>
        <NavLink to="/dashboard">Dashboard</NavLink>
      </nav>
    </header>
  )
}

export default NavBar
