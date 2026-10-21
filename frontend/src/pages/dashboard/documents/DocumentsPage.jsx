import { useCallback, useEffect, useState } from 'react'

import { apiGet, apiPatch, apiPost } from '../../../api/client.js'
import { useAuth } from '../../../context/AuthContext.jsx'
import DocumentTemplateForm from './DocumentTemplateForm.jsx'
import { activeBadge, formatDateTime, mediaFileUrl, requestErrorMessage, splitApiErrors } from './helpers.js'

/*
 * Module Documents : gestion des modèles Word (DocumentTemplate).
 *
 * Backend constaté (documents/views.py + documents/urls.py) :
 *   - URL de liste/création : /api/document-templates/
 *   - URL de détail         : /api/document-templates/<id>/
 *   - Methods supportées    : GET, POST, PUT, PATCH, DELETE (ModelViewSet)
 *   - Permissions           : IsAdministrator (super_admin, administrator)
 *   - queryset             : DocumentTemplate.objects.filter(is_active=True)
 *     → un modèle désactivé disparaît de la liste ET du détail (404),
 *       l'API actuelle ne permet donc pas de le réactiver.
 *
 * Aucun endpoint supplémentaire n'est simulé : seules les opérations
 * réellement exposées par le backend sont proposées.
 */

function DocumentsPage() {
  const { user: currentUser } = useAuth()
  // Même mécanisme d'autorisation frontend que les autres modules
  // (rôle), le backend restant la source de vérité (IsAdministrator).
  const canManage = ['super_admin', 'administrator'].includes(currentUser?.role)

  const [templates, setTemplates] = useState([])
  const [isLoading, setIsLoading] = useState(true)
  const [loadError, setLoadError] = useState('')
  const [loadErrorStatus, setLoadErrorStatus] = useState(null)

  const [view, setView] = useState('list') // 'list' | 'create' | 'edit' | 'details'
  const [current, setCurrent] = useState(null)

  const [actionError, setActionError] = useState('')
  const [actionSuccess, setActionSuccess] = useState('')
  const [isDeactivatingId, setIsDeactivatingId] = useState(null)
  const [isApprovingId, setIsApprovingId] = useState(null)

  const load = useCallback(async () => {
    setIsLoading(true)
    setLoadError('')
    setLoadErrorStatus(null)

    try {
      const data = await apiGet('/document-templates/')
      setTemplates(Array.isArray(data) ? data : [])
    } catch (err) {
      setLoadError(requestErrorMessage(err, 'Impossible de charger les modèles de documents.'))
      setLoadErrorStatus(typeof err?.status === 'number' ? err.status : null)
    } finally {
      setIsLoading(false)
    }
  }, [])

  useEffect(() => {
    load()
  }, [load])

  const resetMessages = () => {
    setActionError('')
    setActionSuccess('')
  }

  const showList = () => {
    resetMessages()
    setView('list')
    setCurrent(null)
  }

  const startCreate = () => {
    resetMessages()
    setCurrent(null)
    setView('create')
  }

  const startEdit = (template) => {
    resetMessages()
    setCurrent(template)
    setView('edit')
  }

  const showDetails = (template) => {
    resetMessages()
    setCurrent(template)
    setView('details')
  }

  const handleCancelForm = () => {
    setActionError('')
    setView('list')
    setCurrent(null)
  }

  const handleSaved = async (saved, { mode }) => {
    setView('list')
    setCurrent(null)

    if (saved && saved.is_active === false) {
      setActionSuccess(
        `Le modèle « ${saved.name} » a été enregistré en état inactif : l'API ne le renvoie plus dans la liste.`,
      )
    } else if (mode === 'create') {
      setActionSuccess(`Modèle « ${saved?.name ?? ''} » enregistré par le serveur.`)
    } else {
      setActionSuccess(`Modèle « ${saved?.name ?? ''} » mis à jour.`)
    }

    // La liste est relue depuis l'API : elle reflète la réponse serveur.
    await load()
  }

  const handleApprove = async (template) => {
  if (!canManage || !template.is_active || template.is_approved) return

  const confirmed = window.confirm(
      `Approuver le modèle « ${template.name} » ?\n\n` +
        'Le serveur vérifiera le fichier DOCX avant de valider son approbation.\n\n' +
        'Continuer ?',
    )
    if (!confirmed) return

    resetMessages()
    setIsApprovingId(template.id)

    try {
      await apiPost(`/document-templates/${template.id}/approve/`, {})
      setActionSuccess(`Le modèle « ${template.name} » a été approuvé.`)
      await load()
    } catch (err) {
      const { general } = splitApiErrors(err)
      setActionError(general)
    } finally {
      setIsApprovingId(null)
    }
  }

  const handleDeactivate = async (template) => {
    if (!canManage) return

    const confirmed = window.confirm(
      `Désactiver le modèle « ${template.name} » ?\n\n` +
        "Attention : ce modèle sera retiré de la liste renvoyée par l'API (filtre " +
        'is_active=True sur la liste et le détail). Il ne pourra pas être réactivé ' +
        "depuis l'application.\n\nContinuer ?",
    )
    if (!confirmed) return

    resetMessages()
    setIsDeactivatingId(template.id)

    try {
      await apiPatch(`/document-templates/${template.id}/`, { is_active: false })
      setActionSuccess(
        `Le modèle « ${template.name} » a été désactivé : l'API ne le renvoie plus. ` +
          'Sa réactivation nécessite une intervention backend.',
      )
      await load()
    } catch (err) {
      const { general } = splitApiErrors(err)
      setActionError(general)
    } finally {
      setIsDeactivatingId(null)
    }
  }

  const renderDetails = (template) => {
    const href = mediaFileUrl(template.file)
    const badge = activeBadge(template.is_active !== false)

    return (
      <div className="card doc-card">
        <div className="dashboard-page-header">
          <div>
            <h3 className="card-title">Détails du modèle</h3>
            <p className="muted">Modèle n° {template.id}</p>
          </div>

          <div className="doc-detail-actions">
            <button type="button" className="btn btn-outline btn-sm" onClick={showList}>
              Retour à la liste
            </button>
            {canManage && (
              <button
                type="button"
                className="btn btn-primary btn-sm"
                onClick={() => startEdit(template)}
              >
                Modifier
              </button>
            )}
          </div>
        </div>

        <dl className="doc-detail-list">
          <dt>Nom</dt>
          <dd>{template.name}</dd>

          <dt>Description</dt>
          <dd>{template.description || <span className="muted">Aucune description.</span>}</dd>

          <dt>État</dt>
          <dd>
            <span className="badge" style={badge.style}>
              {badge.label}
            </span>
          </dd>

          <dt>Créé le</dt>
          <dd>{formatDateTime(template.created_at)}</dd>

          <dt>Dernière modification</dt>
          <dd>{formatDateTime(template.updated_at)}</dd>

          <dt>Fichier Word</dt>
          <dd>
            {href ? (
              <a
                className="btn btn-outline btn-sm"
                href={href}
                download
                aria-label={`Télécharger le fichier Word du modèle ${template.name}`}
              >
                Télécharger le fichier
              </a>
            ) : (
              <span className="muted">Aucun fichier associé.</span>
            )}
          </dd>
        </dl>
      </div>
    )
  }

  const renderList = () => {
    if (templates.length === 0) {
      return (
        <div>
          <p>Aucun modèle de document.</p>
          <p className="muted">
            {canManage
              ? 'Utilisez « Créer un modèle » pour enregistrer un premier fichier Word (.docx).'
              : 'Aucun modèle n’est disponible avec votre rôle.'}
          </p>
        </div>
      )
    }

    return (
      <div className="table-shell doc-list">
        <table>
          <caption className="sr-only">Modèles Word enregistrés dans la clinique</caption>
          <thead>
            <tr>
              <th scope="col">Nom</th>
              <th scope="col">Description</th>
              <th scope="col">Fichier</th>
              <th scope="col">État</th>
              <th scope="col">Dernière modification</th>
              <th scope="col">Actions</th>
            </tr>
          </thead>
          <tbody>
            {templates.map((template) => {
              const href = mediaFileUrl(template.file)
              const badge = activeBadge(template.is_active !== false)

              return (
                <tr key={template.id}>
                  <td data-label="Nom">{template.name}</td>
                  <td data-label="Description">
                    {template.description || <span className="muted">—</span>}
                  </td>
                  <td data-label="Fichier">
                    {href ? (
                      <a
                        href={href}
                        download
                        aria-label={`Télécharger le fichier Word du modèle ${template.name}`}
                      >
                        Télécharger
                      </a>
                    ) : (
                      <span className="muted">Aucun fichier associé</span>
                    )}
                  </td>
                  <td data-label="État">
                    <span className="badge" style={badge.style}>
                      {badge.label}
                    </span>
                  </td>
                  <td data-label="Dernière modification">{formatDateTime(template.updated_at)}</td>
                  <td data-label="Actions" className="table-actions">
                    <button
                      type="button"
                      className="btn btn-outline btn-sm"
                      onClick={() => showDetails(template)}
                    >
                      Détails
                    </button>
                    {canManage && (
                      <button
                        type="button"
                        className="btn btn-outline btn-sm"
                        onClick={() => startEdit(template)}
                        disabled={isDeactivatingId === template.id}
                      >
                        Modifier
                      </button>
                    )}
                    {canManage && template.is_active && !template.is_approved && (
                      <button
                        type="button"
                        className="btn btn-primary btn-sm"
                        onClick={() => handleApprove(template)}
                        disabled={isApprovingId === template.id}
                      >
                        {isApprovingId === template.id ? 'Approbation…' : 'Approuver'}
                      </button>
                    )}
                    {canManage && template.is_active !== false && (
                      <button
                        type="button"
                        className="danger-link"
                        onClick={() => handleDeactivate(template)}
                        disabled={isDeactivatingId === template.id}
                      >
                        {isDeactivatingId === template.id ? 'Désactivation…' : 'Désactiver'}
                      </button>
                    )}
                  </td>
                </tr>
              )
            })}
          </tbody>
        </table>
      </div>
    )
  }

  const showForm = view === 'create' || (view === 'edit' && current)

  let body

  if (showForm) {
    body = (
      <DocumentTemplateForm
        key={view === 'create' ? 'create' : `edit-${current.id}`}
        template={view === 'edit' ? current : null}
        onCancel={handleCancelForm}
        onSaved={handleSaved}
      />
    )
  } else if (isLoading) {
    body = <p>Chargement…</p>
  } else if (loadError) {
    body = (
      <div>
        <pre className="error-text" role="alert" style={{ whiteSpace: 'pre-wrap' }}>
          {loadError}
        </pre>
        {loadErrorStatus !== 403 && (
          <button type="button" className="btn btn-outline btn-sm" onClick={load}>
            Réessayer
          </button>
        )}
      </div>
    )
  } else if (view === 'details' && current) {
    body = renderDetails(current)
  } else {
    body = renderList()
  }

  return (
    <section>
      <div className="dashboard-page-header">
        <div>
          <h2>Documents</h2>
          <p>Gérez les modèles Word utilisés pour les documents de la clinique.</p>
          <p className="muted">
            Source : <code>/api/document-templates/</code>
          </p>
        </div>

        {canManage && !showForm && !isLoading && !loadError && (
          <button type="button" className="btn btn-primary" onClick={startCreate}>
            Créer un modèle
          </button>
        )}
      </div>

      {actionError && (
        <p className="error-text" role="alert">
          {actionError}
        </p>
      )}
      {actionSuccess && (
        <p className="success-text" role="status">
          {actionSuccess}
        </p>
      )}

      {body}
    </section>
  )
}

export default DocumentsPage
