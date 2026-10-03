import { useState } from 'react'
import { Link, useLocation, useNavigate } from 'react-router-dom'

import PageHero from '../components/common/PageHero.jsx'
import { useAuth } from '../context/AuthContext.jsx'

function Login() {
  const navigate = useNavigate()
  const location = useLocation()
  const { login, isAuthenticated } = useAuth()

  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState('')

  const from = location.state?.from?.pathname || '/dashboard'

  const handleSubmit = async (event) => {
    event.preventDefault()
    setError('')

    try {
      await login({ email, password })
      navigate(from, { replace: true })
    } catch (err) {
      setError(err.message)
    }
  }

  return (
    <>
      <PageHero
        eyebrow="Espace sécurisé"
        title="Connexion"
        description="Accès réservé aux membres du cabinet : praticiens, secrétariat et administration."
      />

      <section className="page-shell">
        {isAuthenticated ? (
          <>
            <h2>Vous êtes déjà connecté.</h2>
            <p className="muted">Votre session est active sur cet appareil.</p>
            <div className="hero-actions">
              <button type="button" className="btn btn-primary" onClick={() => navigate('/dashboard')}>
                Aller au dashboard
              </button>
              <Link className="btn btn-outline" to="/">
                Retour au site
              </Link>
            </div>
          </>
        ) : (
          <form className="form-shell" onSubmit={handleSubmit}>
            <label>
              Email
              <input
                type="email"
                value={email}
                onChange={(event) => setEmail(event.target.value)}
                autoComplete="username"
                required
              />
            </label>

            <label>
              Mot de passe
              <input
                type="password"
                value={password}
                onChange={(event) => setPassword(event.target.value)}
                autoComplete="current-password"
                required
              />
            </label>

            <button type="submit">Se connecter</button>

            {error && <p className="error-text">{error}</p>}

            <p className="contact-note">
              Mot de passe oublié ? Contactez l’administration du cabinet.
            </p>
          </form>
        )}
      </section>
    </>
  )
}

export default Login
