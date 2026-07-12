import { useState } from 'react'
import { useLocation, useNavigate } from 'react-router-dom'

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

  if (isAuthenticated) {
    return (
      <section className="page-shell">
        <h1>Connexion</h1>
        <p>Vous êtes déjà connecté.</p>
        <button type="button" onClick={() => navigate('/dashboard')}>
          Aller au dashboard
        </button>
      </section>
    )
  }

  return (
    <section className="page-shell">
      <h1>Connexion</h1>
      <form className="form-shell" onSubmit={handleSubmit}>
        <label>
          Email
          <input
            type="email"
            value={email}
            onChange={(event) => setEmail(event.target.value)}
            required
          />
        </label>
        <label>
          Mot de passe
          <input
            type="password"
            value={password}
            onChange={(event) => setPassword(event.target.value)}
            required
          />
        </label>
        <button type="submit">Se connecter</button>
        {error && <p className="error-text">{error}</p>}
      </form>
    </section>
  )
}

export default Login
