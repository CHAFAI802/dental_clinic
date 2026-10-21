import { useRef, useState } from 'react'

import { apiPatch, apiPost } from '../../../api/client.js'
import { formatFileSize, splitApiErrors } from './helpers.js'

/*
 * Backend : DocumentTemplateViewSet (viewsets.ModelViewSet)
 *           permission_classes = [IsAdministrator]
 *           queryset = DocumentTemplate.objects.filter(is_active=True)
 *
 * Champs (DocumentTemplateSerializer) :
 *   - name        : obligatoire, CharField(max_length=255)
 *   - description : facultatif
 *   - file        : facultatif (blank=True, null=True), extension .docx
 *                   validée par validate_file côté serveur
 *   - is_active   : booléen, défaut true
 *   - id, created_at, updated_at : lecture seule
 *
 * Le fichier est envoyé en multipart/form-data : api/client.js laisse le
 * navigateur générer la frontière quand le corps est une instance
 * FormData (aucun en-tête Content-Type défini manuellement).
 */

const MAX_NAME_LENGTH = 255
const DOCX_ACCEPT =
  '.docx,application/vnd.openxmlformats-officedocument.wordprocessingml.document'

const DEACTIVATION_WARNING =
  "Attention : un modèle inactif n'est plus renvoyé par l'API des modèles " +
  '(liste ET détail filtrées sur is_active=True). Il deviendra invisible ' +
  "dans l'application et ne pourra pas être réactivé depuis celle-ci."

function hasDocxExtension(file) {
  return Boolean(file && typeof file.name === 'string' && file.name.toLowerCase().endsWith('.docx'))
}

function DocumentTemplateForm({ template, onCancel, onSaved }) {
  const isEdit = Boolean(template)

  const [name, setName] = useState(template?.name ?? '')
  const [description, setDescription] = useState(template?.description ?? '')
  const [isActive, setIsActive] = useState(template ? template.is_active !== false : true)
  const [file, setFile] = useState(null)
  const [errors, setErrors] = useState({})
  const [isSubmitting, setIsSubmitting] = useState(false)

  const fileInputRef = useRef(null)

  const initialName = template?.name ?? ''
  const initialDescription = template?.description ?? ''
  const initialIsActive = template ? template.is_active !== false : true
  const isDirty =
    name !== initialName ||
    description !== initialDescription ||
    isActive !== initialIsActive ||
    file !== null

  const setFieldError = (field, message) => {
    setErrors((current) => ({ ...current, [field]: message }))
  }

  const clearAllErrors = () => setErrors({})

  const handleFileChange = (event) => {
    const selected = event.target.files && event.target.files[0]

    if (!selected) return

    // On ne nettoie que l'erreur du champ fichier : les erreurs de saisie
    // des autres champs restent visibles jusqu'à la prochaine soumission.
    setErrors((current) => {
      const next = { ...current }
      delete next.file
      return next
    })
    setFile(selected)

    if (!hasDocxExtension(selected)) {
      setFieldError(
        'file',
        'Extension non prise en charge : seuls les fichiers .docx (Microsoft Word) sont acceptés. ' +
          "Vérification d'extension uniquement : le contrôle du contenu est effectué par le serveur.",
      )
    }
  }

  const removeFile = () => {
    setFile(null)
    if (fileInputRef.current) fileInputRef.current.value = ''
    setErrors((current) => {
      const next = { ...current }
      delete next.file
      return next
    })
  }

  const handleCancel = () => {
    if (isDirty) {
      const confirmed = window.confirm(
        'Abandonner ce formulaire ? Les modifications non enregistrées seront perdues.',
      )
      if (!confirmed) return
    }

    onCancel()
  }

  const handleSubmit = async (event) => {
    event.preventDefault()

    const trimmedName = name.trim()
    const nextErrors = {}

    if (!trimmedName) {
      nextErrors.name = 'Le nom est obligatoire.'
    } else if (trimmedName.length > MAX_NAME_LENGTH) {
      nextErrors.name = `Le nom ne peut pas dépasser ${MAX_NAME_LENGTH} caractères.`
    }

    if (file && !hasDocxExtension(file)) {
      nextErrors.file =
        'Le fichier sélectionné ne possède pas l’extension .docx. Sélectionnez un document Word.'
    }

    if (Object.keys(nextErrors).length > 0) {
      setErrors(nextErrors)
      return
    }

    // Un modèle inactif devient invisible : l'utilisateur doit le confirmer.
    if (!isActive) {
      const confirmed = window.confirm(
        `${isEdit ? 'Désactiver' : 'Créer'} ce modèle en état inactif ?\n\n${DEACTIVATION_WARNING}`,
      )
      if (!confirmed) return
    }

    clearAllErrors()
    setIsSubmitting(true)

    try {
      const payload = {
        name: trimmedName,
        description: description.trim(),
        is_active: isActive,
      }

      let saved

      if (isEdit) {
        if (file) {
          // Nouveau fichier : multipart (PATCH partiel, le fichier actuel
          // est remplacé par le nouveau, les autres champs restent identiques).
          const form = new FormData()
          form.append('name', payload.name)
          form.append('description', payload.description)
          form.append('is_active', String(payload.is_active))
          form.append('file', file)
          saved = await apiPatch(`/document-templates/${template.id}/`, form)
        } else {
          // Sans nouveau fichier : JSON sans clé « file » → le fichier
          // existant est conservé par PATCH (mise à jour partielle).
          saved = await apiPatch(`/document-templates/${template.id}/`, payload)
        }
      } else {
        const form = new FormData()
        form.append('name', payload.name)
        form.append('description', payload.description)
        form.append('is_active', String(payload.is_active))
        if (file) form.append('file', file)
        saved = await apiPost('/document-templates/', form)
      }

      onSaved(saved, { mode: isEdit ? 'edit' : 'create' })
    } catch (err) {
      const { fields, general } = splitApiErrors(err)
      setErrors({ ...fields, ...(general ? { form: general } : {}) })
      // Les données saisies sont conservées pour éviter une nouvelle saisie.
    } finally {
      setIsSubmitting(false)
    }
  }

  return (
    <div className="card doc-card">
      <h3 className="card-title">{isEdit ? 'Modifier le modèle' : 'Créer un modèle'}</h3>

      <form className="form-shell doc-form" onSubmit={handleSubmit} noValidate>
        <label htmlFor="doc-template-name">
          Nom
          <input
            id="doc-template-name"
            type="text"
            value={name}
            maxLength={MAX_NAME_LENGTH}
            onChange={(event) => setName(event.target.value)}
            required
          />
        </label>
        {errors.name && (
          <p className="error-text" role="alert">
            {errors.name}
          </p>
        )}

        <label htmlFor="doc-template-description">
          Description (facultatif)
          <textarea
            id="doc-template-description"
            rows={3}
            value={description}
            onChange={(event) => setDescription(event.target.value)}
          />
        </label>

        <div className="doc-file-field">
          <label htmlFor="doc-template-file">
            Fichier Word (.docx) {isEdit ? '— facultatif, conserve le fichier actuel si vide' : '— facultatif'}
          </label>

          <input
            id="doc-template-file"
            ref={fileInputRef}
            type="file"
            accept={DOCX_ACCEPT}
            style={file ? { display: 'none' } : undefined}
            onClick={(event) => {
              // Permet de resélectionner le même fichier après un retrait.
              event.currentTarget.value = ''
            }}
            onChange={handleFileChange}
          />

          {file ? (
            <div className="file-selection">
              <div className="file-selection-info">
                <strong className="file-selection-name" title={file.name}>
                  {file.name}
                </strong>
                <span className="muted"> — {formatFileSize(file.size)}</span>
              </div>
              <div className="file-selection-actions">
                <button
                  type="button"
                  className="btn btn-outline btn-sm"
                  onClick={() => fileInputRef.current && fileInputRef.current.click()}
                >
                  Choisir un autre fichier
                </button>
                <button type="button" className="danger-link" onClick={removeFile}>
                  Retirer le fichier
                </button>
              </div>
            </div>
          ) : (
            <p className="muted">
              Sélectionnez un document .docx préparé dans Word ou LibreOffice. La mise en page du
              fichier (marges, en-têtes, images, tableaux, couleurs…) est conservée telle quelle.
            </p>
          )}
        </div>
        {errors.file && (
          <p className="error-text" role="alert">
            {errors.file}
          </p>
        )}

        <label className="checkbox-row">
          <input
            type="checkbox"
            checked={isActive}
            onChange={(event) => setIsActive(event.target.checked)}
          />
          Modèle actif
        </label>
        {!isActive && (
          <p className="doc-warning" role="alert">
            {DEACTIVATION_WARNING}
          </p>
        )}

        <div className="doc-form-actions">
          <button type="submit" className="btn btn-primary" disabled={isSubmitting}>
            {isSubmitting ? 'Enregistrement…' : 'Enregistrer'}
          </button>
          <button
            type="button"
            className="btn btn-outline doc-form-cancel"
            onClick={handleCancel}
            disabled={isSubmitting}
          >
            Annuler
          </button>
        </div>

        {errors.form && (
          <pre className="error-text" role="alert" style={{ whiteSpace: 'pre-wrap' }}>
            {errors.form}
          </pre>
        )}
      </form>
    </div>
  )
}

export default DocumentTemplateForm
