import { useEffect, useState } from 'react'

import { apiDelete, apiGet, apiPatch, apiPost } from '../../../api/client.js'
import { useAuth } from '../../../context/AuthContext.jsx'
import { activeBadge, formatDate } from './helpers.js'

const EMPTY_FORM = { name: '', code: '', is_active: true }

/*
 * Backend : PrestationCategoryViewSet (viewsets.ModelViewSet)
 *           permission_classes = [IsAdministrator]
 *           → super_admin, administrator sur toutes les actions
 *             (list, retrieve, create, update, partial_update, destroy).
 *
 * Champs (PrestationCategorySerializer) :
 *   - name      : obligatoire, unique
 *   - code      : obligatoire, unique
 *   - is_active : booléen, défaut true
 *   - id, created_at, updated_at : lecture seule
 */
function PrestationCategoriesPage() {
  const { user: currentUser } = useAuth()

  const canManage = ['super_admin', 'administrator'].includes(currentUser?.role)

  const [categories, setCategories] = useState([])
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState('')

  const [formValues, setFormValues] = useState(EMPTY_FORM)
  const [editingId, setEditingId] = useState(null)
  const [isSaving, setIsSaving] = useState(false)
  const [deletingId, setDeletingId] = useState(null)
  const [actionError, setActionError] = useState('')
  const [actionSuccess, setActionSuccess] = useState('')

  const load = async () => {
    setIsLoading(true)
    setError('')

    try {
      const data = await apiGet('/prestation-categories/')
      setCategories(Array.isArray(data) ? data : [])
    } catch (err) {
      setError(err.message)
    } finally {
      setIsLoading(false)
    }
  }

  useEffect(() => {
    load()
    // Chargement initial de la page.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  const setField = (field, value) => {
    setActionSuccess('')
    setActionError('')
    setFormValues((current) => ({ ...current, [field]: value }))
  }

  const resetForm = () => {
    setFormValues(EMPTY_FORM)
    setEditingId(null)
  }

  const handleSubmit = async (event) => {
    event.preventDefault()

    if (!canManage) return

    setActionError('')
    setActionSuccess('')

    const payload = {
      name: formValues.name.trim(),
      code: formValues.code.trim(),
      is_active: Boolean(formValues.is_active),
    }

    if (!payload.name) {
      setActionError('Le nom est obligatoire.')
      return
    }

    if (!payload.code) {
      setActionError('Le code est obligatoire.')
      return
    }

    setIsSaving(true)

    try {
      if (editingId === null) {
        const created = await apiPost('/prestation-categories/', payload)
        setCategories((current) => [...current, created])
        setActionSuccess('Catégorie créée.')
      } else {
        const updated = await apiPatch(`/prestation-categories/${editingId}/`, payload)
        setCategories((current) =>
          current.map((category) => (category.id === updated.id ? updated : category)),
        )
        setActionSuccess('Catégorie mise à jour.')
      }

      resetForm()
    } catch (err) {
      setActionError(err.message)
    } finally {
      setIsSaving(false)
    }
  }

  const handleEdit = (category) => {
    setActionError('')
    setActionSuccess('')
    setEditingId(category.id)
    setFormValues({
      name: category.name || '',
      code: category.code || '',
      is_active: category.is_active !== false,
    })
  }

  const handleDelete = async (category) => {
    if (!canManage) return

    const confirmed = window.confirm(
      `Confirmer la suppression de la catégorie « ${category.code} - ${category.name} » ?`,
    )
    if (!confirmed) return

    setActionError('')
    setActionSuccess('')
    setDeletingId(category.id)

    try {
      await apiDelete(`/prestation-categories/${category.id}/`)
      setCategories((current) => current.filter((item) => item.id !== category.id))

      if (editingId === category.id) resetForm()

      setActionSuccess('Catégorie supprimée.')
    } catch (err) {
      setActionError(err.message)
    } finally {
      setDeletingId(null)
    }
  }

  if (isLoading) {
    return (
      <section>
        <h2>Catégories de prestations</h2>
        <p>Chargement…</p>
      </section>
    )
  }

  if (error) {
    return (
      <section>
        <div className="dashboard-page-header">
          <div>
            <h2>Catégories de prestations</h2>
            <p>
              Source : <code>/api/prestation-categories/</code>
            </p>
          </div>
        </div>
        <p className="error-text">{error}</p>
      </section>
    )
  }

  return (
    <section>
      <div className="dashboard-page-header">
        <div>
          <h2>Catégories de prestations</h2>
          <p>Source : <code>/api/prestation-categories/</code></p>
        </div>
      </div>

      {actionError && <p className="error-text">{actionError}</p>}
      {actionSuccess && <p className="success-text">{actionSuccess}</p>}

      {canManage && (
        <div className="card" style={{ marginBottom: 'var(--space-5)' }}>
          <h3 className="card-title">
            {editingId === null ? 'Créer une catégorie' : 'Modifier la catégorie'}
          </h3>

          <form className="form-shell" onSubmit={handleSubmit}>
            <div className="form-row">
              <label>
                Nom
                <input
                  type="text"
                  value={formValues.name}
                  onChange={(event) => setField('name', event.target.value)}
                  required
                />
              </label>

              <label>
                Code
                <input
                  type="text"
                  value={formValues.code}
                  onChange={(event) => setField('code', event.target.value)}
                  required
                />
              </label>

              <label className="checkbox-row">
                <input
                  type="checkbox"
                  checked={Boolean(formValues.is_active)}
                  onChange={(event) => setField('is_active', event.target.checked)}
                />
                Catégorie active
              </label>
            </div>

            <div className="table-actions">
              <button type="submit" disabled={isSaving}>
                {isSaving
                  ? 'Enregistrement…'
                  : editingId === null
                    ? 'Créer'
                    : 'Enregistrer'}
              </button>

              {editingId !== null && (
                <button type="button" className="btn btn-outline" onClick={resetForm}>
                  Annuler
                </button>
              )}
            </div>
          </form>
        </div>
      )}

      {categories.length === 0 ? (
        <p>Aucune catégorie de prestation.</p>
      ) : (
        <div className="table-shell">
          <table>
            <thead>
              <tr>
                <th>Code</th>
                <th>Nom</th>
                <th>Statut</th>
                <th>Créée le</th>
                {canManage && <th>Actions</th>}
              </tr>
            </thead>
            <tbody>
              {categories.map((category) => {
                const badge = activeBadge(category.is_active !== false)

                return (
                  <tr key={category.id}>
                    <td>{category.code}</td>
                    <td>{category.name}</td>
                    <td>
                      <span className="badge" style={badge.style}>
                        {badge.label}
                      </span>
                    </td>
                    <td>{formatDate(category.created_at)}</td>
                    {canManage && (
                      <td className="table-actions">
                        <button
                          type="button"
                          className="btn btn-outline btn-sm"
                          onClick={() => handleEdit(category)}
                        >
                          Modifier
                        </button>
                        <button
                          type="button"
                          className="danger-link"
                          onClick={() => handleDelete(category)}
                          disabled={deletingId === category.id}
                        >
                          {deletingId === category.id ? 'Suppression…' : 'Supprimer'}
                        </button>
                      </td>
                    )}
                  </tr>
                )
              })}
            </tbody>
          </table>
        </div>
      )}
    </section>
  )
}

export default PrestationCategoriesPage
