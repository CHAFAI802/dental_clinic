import { useEffect, useState } from 'react'
import { Link, useNavigate, useParams } from 'react-router-dom'

import { apiGet, apiPatch } from '../../../api/client.js'
import { useAuth } from '../../../context/AuthContext.jsx'
import UserForm from './UserForm.jsx'

function UserEditPage() {
  const { userId } = useParams()
  const navigate = useNavigate()
  const { user: currentUser } = useAuth()

  const canManageUsers = currentUser?.role === 'super_admin'

  const [targetUser, setTargetUser] = useState(null)
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState('')

  useEffect(() => {
    let isMounted = true

    const run = async () => {
      setIsLoading(true)
      setError('')
      try {
        const data = await apiGet(`/users/${userId}/`)
        if (isMounted) {
          setTargetUser(data)
        }
      } catch (err) {
        if (isMounted) {
          setError(err.message)
        }
      } finally {
        if (isMounted) {
          setIsLoading(false)
        }
      }
    }

    run()

    return () => {
      isMounted = false
    }
  }, [userId])

  const handleSubmit = async (payload) => {
    await apiPatch(`/users/${userId}/`, payload)
    navigate('/dashboard/users', { replace: true })
  }

  return (
    <section>
      <div className="dashboard-page-header">
        <div>
          <h2>Utilisateur</h2>
          <p>
            <Link to="/dashboard/users">← Retour</Link>
          </p>
        </div>
      </div>

      {isLoading ? (
        <p>Chargement…</p>
      ) : error ? (
        <pre className="error-text" style={{ whiteSpace: 'pre-wrap' }}>
          {error}
        </pre>
      ) : !targetUser ? (
        <p>Utilisateur introuvable.</p>
      ) : canManageUsers ? (
        <>
          <p>
            Modification du compte : <strong>{targetUser.email}</strong>
          </p>
          <UserForm
            initialValues={targetUser}
            requirePassword={false}
            submitLabel="Enregistrer"
            onSubmit={handleSubmit}
          />
        </>
      ) : (
        <>
          <p>
            <strong>{targetUser.first_name} {targetUser.last_name}</strong>
          </p>
          <ul>
            <li>Email : {targetUser.email}</li>
            <li>Rôle : {targetUser.role}</li>
            <li>Actif : {targetUser.is_active ? 'Oui' : 'Non'}</li>
          </ul>
          <p className="error-text">Vous n’avez pas les droits pour modifier les comptes.</p>
        </>
      )}
    </section>
  )
}

export default UserEditPage
