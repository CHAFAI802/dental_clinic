import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'

import { apiDelete, apiGet } from '../../../api/client.js'
import TableShell from '../../../components/dashboard/TableShell.jsx'
import {
  filterTableRows,
  paginateTableRows,
  TablePagination,
  TableSearch,
} from '../../../components/dashboard/TableControls.jsx'
import { useAuth } from '../../../context/AuthContext.jsx'

function UsersListPage() {
  const { user: currentUser } = useAuth()
  const canManageUsers = currentUser?.role === 'super_admin'

  const [users, setUsers] = useState([])
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState('')
  const [isDeletingId, setIsDeletingId] = useState(null)
  const [search, setSearch] = useState('')
  const [page, setPage] = useState(1)
  const [pageSize, setPageSize] = useState(10)

  const load = async () => {
    setIsLoading(true)
    setError('')
    try {
      const data = await apiGet('/users/')
      setUsers(Array.isArray(data) ? data : [])
    } catch (err) {
      setError(err.message)
    } finally {
      setIsLoading(false)
    }
  }

  useEffect(() => {
    load()
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  const handleDelete = async (targetUser) => {
    if (!canManageUsers) return

    const confirmed = window.confirm(
      `Confirmer la suppression définitive du compte : ${targetUser.email} ?`,
    )
    if (!confirmed) return

    setIsDeletingId(targetUser.id)
    setError('')
    try {
      await apiDelete(`/users/${targetUser.id}/`)
      await load()
    } catch (err) {
      setError(err.message)
    } finally {
      setIsDeletingId(null)
    }
  }

  const filteredUsers = filterTableRows(users, search, (user) => [
    user.first_name,
    user.last_name,
    `${user.first_name || ''} ${user.last_name || ''}`,
    user.email,
    user.role,
    user.is_active ? 'actif oui' : 'inactif non',
  ])
  const { items: displayedUsers, currentPage } = paginateTableRows(
    filteredUsers,
    page,
    pageSize,
  )

  return (
    <section>
      <div className="dashboard-page-header">
        <div>
          <h2>Utilisateurs</h2>
          <p>Source : <code>/api/users/</code></p>
        </div>

        {canManageUsers && (
          <Link className="button-link" to="/dashboard/users/new">
            Créer un utilisateur
          </Link>
        )}
      </div>

      {isLoading ? (
        <p>Chargement…</p>
      ) : error ? (
        <pre className="error-text" style={{ whiteSpace: 'pre-wrap' }}>
          {error}
        </pre>
      ) : users.length === 0 ? (
        <p>Aucun utilisateur.</p>
      ) : (
        <>
          <TableSearch
            value={search}
            onChange={(value) => {
              setSearch(value)
              setPage(1)
            }}
            label="Rechercher un utilisateur"
            placeholder="Rechercher par nom, email ou rôle…"
          />
          {filteredUsers.length === 0 ? (
            <p>Aucun utilisateur correspondant.</p>
          ) : (
            <>
              <TableShell>
                <table>
                  <thead>
                    <tr>
                      <th>Nom</th>
                      <th>Email</th>
                      <th>Rôle</th>
                      <th>Actif</th>
                      <th>Actions</th>
                    </tr>
                  </thead>
                  <tbody>
                    {displayedUsers.map((u) => (
                      <tr key={u.id}>
                        <td>{u.first_name} {u.last_name}</td>
                        <td>{u.email}</td>
                        <td>{u.role}</td>
                        <td>{u.is_active ? 'Oui' : 'Non'}</td>
                        <td className="table-actions">
                          <Link to={`/dashboard/users/${u.id}`}>{canManageUsers ? 'Modifier' : 'Voir'}</Link>
                          {canManageUsers && (
                            <button
                              type="button"
                              className="danger-link"
                              onClick={() => handleDelete(u)}
                              disabled={isDeletingId === u.id}
                            >
                              {isDeletingId === u.id ? 'Suppression…' : 'Supprimer'}
                            </button>
                          )}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </TableShell>
              <TablePagination
                page={currentPage}
                pageSize={pageSize}
                totalItems={filteredUsers.length}
                onPageChange={setPage}
                onPageSizeChange={(size) => {
                  setPageSize(size)
                  setPage(1)
                }}
                label="des utilisateurs"
              />
            </>
          )}
        </>
      )}
    </section>
  )
}

export default UsersListPage
