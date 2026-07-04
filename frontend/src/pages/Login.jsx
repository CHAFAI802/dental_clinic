import { useState } from 'react'

function Login() {
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState('')

  const handleSubmit = async (event) => {
    event.preventDefault()
    setError('')

    try {
      const response = await fetch('http://localhost:8000/api/auth/login/', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email, password }),
      })

      const data = await response.json()
      if (!response.ok) {
        throw new Error(data.detail || 'Login failed')
      }

      localStorage.setItem('authToken', data.token)
      window.location.href = 'http://localhost:5173/app/'
    } catch (err) {
      setError(err.message)
    }
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
