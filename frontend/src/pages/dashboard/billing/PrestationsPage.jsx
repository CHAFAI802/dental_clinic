import { useEffect, useMemo, useState } from 'react'

import { apiDelete, apiGet, apiPatch, apiPost } from '../../../api/client.js'
import { useAuth } from '../../../context/AuthContext.jsx'
import { activeBadge, formatDate } from './helpers.js'

const EMPTY_FORM = {
  category: '',
  code: '',
  label: '',
  description: '',
  is_active: true,
}

/*
 * Backend : PrestationViewSet (viewsets.ModelViewSet)
 *           permission_classes = [IsAdministrator]
 *           → super_admin, administrator sur toutes les actions.
 *
 * Champs (PrestationSerializer) :
 *   - category    : obligatoire (clé étrangère vers PrestationCategory)
 *   - code        : obligatoire, unique
 *   - label       : obligatoire
 *   - description : facultatif (blank=True)
 *   - is_active   : booléen, défaut true
 *   - id, created_at, updated_at : lecture seule
 *
 * La relation catégorie → prestation est exposée sous forme d'identifiants :
 * les libellés sont récupérés via /api/prestation-categories/ (jamais inventés).
 */
function PrestationsPage() {
  const { user: currentUser } = useAuth()

  const canManage = ['super_admin', 'administrator'].includes(currentUser?.role)

  const [prestations, setPrestations] = useState([])
  const [categories, setCategories] = useState([])
  const [categoriesUnavailable, setCategoriesUnavailable] = useState(false)

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
    setCategoriesUnavailable(false)

    let prestationData

    try {
      prestationData = await apiGet('/prestations/')
    } catch (err) {
      setError(err.message)
      setIsLoading(false)
      return
    }

    setPrestations(Array.isArray(prestationData) ? prestationData : [])

    // Les libellés de catégorie ne sont qu'un enrichissement d'affichage :
    // leur échec n'empêche pas l'affichage des prestations.
    try {
      const categoriesData = await apiGet('/prestation-categories/')
      setCategories(Array.isArray(categoriesData) ? categoriesData : [])
    } catch {
      setCategoriesUnavailable(true)
    }

    setIsLoading(false)
  }

  useEffect(() => {
    load()
    // Chargement initial de la page.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  const categoryById = useMemo(
    () => new Map(categories.map((category) => [category.id, category])),
    [categories],
  )

  const categoryLabel = (categoryId) => {
    if (categoryId === null || categoryId === undefined) return '-'
    const category = categoryById.get(categoryId)
    return category ? `${category.code} - ${category.name}` : `#${categoryId}`
  }

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
      category: Number(formValues.category),
      code: formValues.code.trim(),
      label: formValues.label.trim(),
      description: formValues.description,
      is_active: Boolean(formValues.is_active),
    }

    if (!formValues.category) {
      setActionError('Sélectionnez une catégorie.')
      return
    }

    if (!payload.code) {
      setActionError('Le code est obligatoire.')
      return
    }

    if (!payload.label) {
      setActionError('Le libellé est obligatoire.')
      return
    }

    setIsSaving(true)

    try {
      if (editingId === null) {
        const created = await apiPost('/prestations/', payload)
        setPrestations((current) => [...current, created])
        setActionSuccess('Prestation créée.')
      } else {
        const updated = await apiPatch(`/prestations/${editingId}/`, payload)
        setPrestations((current) =>
          current.map((prestation) => (prestation.id === updated.id ? updated : prestation)),
        )
        setActionSuccess('Prestation mise à jour.')
      }

      resetForm()
    } catch (err) {
      setActionError(err.message)
    } finally {
      setIsSaving(false)
    }
  }

  const handleEdit = (prestation) => {
    setActionError('')
    setActionSuccess('')
    setEditingId(prestation.id)
    setFormValues({
      category: prestation.category === null || prestation.category === undefined
        ? ''
        : String(prestation.category),
      code: prestation.code || '',
      label: prestation.label || '',
      description: prestation.description || '',
      is_active: prestation.is_active !== false,
    })
  }

  const handleDelete = async (prestation) => {
    if (!canManage) return

    const confirmed = window.confirm(
      `Confirmer la suppression de la prestation « ${prestation.code} - ${prestation.label} » ?`,
    )
    if (!confirmed) return

    setActionError('')
    setActionSuccess('')
    setDeletingId(prestation.id)

    try {
      await apiDelete(`/prestations/${prestation.id}/`)
      setPrestations((current) => current.filter((item) => item.id !== prestation.id))

      if (editingId === prestation.id) resetForm()

      setActionSuccess('Prestation supprimée.')
    } catch (err) {
      setActionError(err.message)
    } finally {
      setDeletingId(null)
    }
  }

  if (isLoading) {
    return (
      <section>
        <h2>Prestations</h2>
        <p>Chargement…</p>
      </section>
    )
  }

  if (error) {
    return (
      <section>
        <div className="dashboard-page-header">
          <div>
            <h2>Prestations</h2>
            <p>
              Source : <code>/api/prestations/</code>
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
          <h2>Prestations</h2>
          <p>Source : <code>/api/prestations/</code></p>
        </div>
      </div>

      {actionError && <p className="error-text">{actionError}</p>}
      {actionSuccess && <p className="success-text">{actionSuccess}</p>}

      {canManage && (
        <div className="card" style={{ marginBottom: 'var(--space-5)' }}>
          <h3 className="card-title">
            {editingId === null ? 'Créer une prestation' : 'Modifier la prestation'}
          </h3>

          <form className="form-shell" onSubmit={handleSubmit}>
            <div className="form-row">
              <label>
                Catégorie
                <select
                  value={formValues.category}
                  onChange={(event) => setField('category', event.target.value)}
                  required
                  disabled={categories.length === 0}
                >
                  <option value="">
                    {categories.length === 0
                      ? 'Aucune catégorie disponible'
                      : 'Sélectionner une catégorie'}
                  </option>
                  {categories.map((category) => (
                    <option key={category.id} value={category.id}>
                      {category.code} - {category.name}
                      {category.is_active === false ? ' (inactive)' : ''}
                    </option>
                  ))}
                </select>
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

              <label>
                Libellé
                <input
                  type="text"
                  value={formValues.label}
                  onChange={(event) => setField('label', event.target.value)}
                  required
                />
              </label>
            </div>

            <label>
              Description
              <textarea
                rows={3}
                value={formValues.description}
                onChange={(event) => setField('description', event.target.value)}
              />
            </label>

            <label className="checkbox-row">
              <input
                type="checkbox"
                checked={Boolean(formValues.is_active)}
                onChange={(event) => setField('is_active', event.target.checked)}
              />
              Prestation active
            </label>

            <div className="table-actions">
              <button
                type="submit"
                disabled={isSaving || categories.length === 0}
              >
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

          {categoriesUnavailable && (
            <p className="muted" style={{ marginBottom: 0 }}>
              Catégories indisponibles (erreur API) : la création et la
              modification sont momentanément impossible.
            </p>
          )}
        </div>
      )}

      {prestations.length === 0 ? (
        <p>Aucune prestation.</p>
      ) : (
        <div className="table-shell">
          <table>
            <thead>
              <tr>
                <th>Code</th>
                <th>Libellé</th>
                <th>Catégorie</th>
                <th>Description</th>
                <th>Statut</th>
                <th>Créée le</th>
                {canManage && <th>Actions</th>}
              </tr>
            </thead>
            <tbody>
              {prestations.map((prestation) => {
                const badge = activeBadge(prestation.is_active !== false)

                return (
                  <tr key={prestation.id}>
                    <td>{prestation.code}</td>
                    <td>{prestation.label}</td>
                    <td>{categoryLabel(prestation.category)}</td>
                    <td style={{ whiteSpace: 'pre-wrap' }}>
                      {prestation.description || '-'}
                    </td>
                    <td>
                      <span className="badge" style={badge.style}>
                        {badge.label}
                      </span>
                    </td>
                    <td>{formatDate(prestation.created_at)}</td>
                    {canManage && (
                      <td className="table-actions">
                        <button
                          type="button"
                          className="btn btn-outline btn-sm"
                          onClick={() => handleEdit(prestation)}
                        >
                          Modifier
                        </button>
                        <button
                          type="button"
                          className="danger-link"
                          onClick={() => handleDelete(prestation)}
                          disabled={deletingId === prestation.id}
                        >
                          {deletingId === prestation.id ? 'Suppression…' : 'Supprimer'}
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

export default PrestationsPage
