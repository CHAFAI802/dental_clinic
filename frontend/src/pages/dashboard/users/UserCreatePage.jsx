import { useNavigate } from 'react-router-dom'

import { apiPost } from '../../../api/client.js'
import { useAuth } from '../../../context/AuthContext.jsx'
import UserForm from './UserForm.jsx'

function UserCreatePage() {
  const navigate = useNavigate()
  const { user: currentUser } = useAuth()

  const canManageUsers = currentUser?.role === 'super_admin'

  if (!canManageUsers) {
    return (
      <section>
        <h2>Création utilisateur</h2>
        <p className="error-text">Accès refusé. Seul un super admin peut créer des comptes.</p>
      </section>
    )
  }

  const handleSubmit = async (payload) => {
    await apiPost('/users/', payload)
    navigate('/dashboard/users', { replace: true })
  }

  return (
    <section>
      <h2>Créer un utilisateur</h2>
      <UserForm requirePassword submitLabel="Créer" onSubmit={handleSubmit} />
    </section>
  )
}

export default UserCreatePage
