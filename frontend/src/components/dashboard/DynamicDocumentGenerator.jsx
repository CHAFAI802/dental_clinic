import { useEffect, useRef, useState } from 'react'

import { apiDownload, apiGet } from '../../api/client.js'

function errorMessage(error) {
  if (error?.status === 401) {
    return 'Session expirée ou authentification invalide. Connectez-vous à nouveau.'
  }
  if (error?.status === 403) {
    return "Votre rôle ne permet pas de générer ce type de document."
  }
  if (!error?.status && !error?.data) {
    return 'Erreur réseau : le serveur est injoignable.'
  }
  return error?.message || 'La génération du document a échoué.'
}

function DynamicDocumentGenerator({
  documentType,
  objectId,
  objectLabel,
  title,
  previewDocument = false,
}) {
  const [templates, setTemplates] = useState([])
  const [selectedTemplateId, setSelectedTemplateId] = useState('')
  const [isLoadingTemplates, setIsLoadingTemplates] = useState(true)
  const [templateError, setTemplateError] = useState('')
  const [isGenerating, setIsGenerating] = useState(false)
  const [generationError, setGenerationError] = useState('')
  const [generationSuccess, setGenerationSuccess] = useState('')
  const [generatedDocument, setGeneratedDocument] = useState(null)
  const [isRenderingPreview, setIsRenderingPreview] = useState(false)
  const [previewError, setPreviewError] = useState('')
  const previewFrameRef = useRef(null)

  useEffect(() => {
    let active = true
    setIsLoadingTemplates(true)
    setTemplateError('')
    setSelectedTemplateId('')

    apiGet(`/document-templates/available/?document_type=${encodeURIComponent(documentType)}`)
      .then((result) => {
        if (active) setTemplates(Array.isArray(result) ? result : [])
      })
      .catch((error) => {
        if (active) setTemplateError(errorMessage(error))
      })
      .finally(() => {
        if (active) setIsLoadingTemplates(false)
      })

    return () => {
      active = false
    }
  }, [documentType])

  useEffect(() => {
    if (!previewDocument || !generatedDocument) return undefined

    let active = true
    const renderPreview = async () => {
      setIsRenderingPreview(true)
      setPreviewError('')

      try {
        const previewDocumentElement = previewFrameRef.current?.contentDocument
        if (!previewDocumentElement) {
          throw new Error('Le cadre de prévisualisation est indisponible.')
        }

        previewDocumentElement.open()
        previewDocumentElement.write(
          '<!doctype html><html><head><meta charset="utf-8">' +
            '<meta name="viewport" content="width=device-width, initial-scale=1">' +
            '</head><body></body></html>',
        )
        previewDocumentElement.close()

        const { renderAsync } = await import('docx-preview')
        await renderAsync(
          generatedDocument.blob,
          previewDocumentElement.body,
          previewDocumentElement.head,
          {
            breakPages: true,
            renderHeaders: true,
            renderFooters: true,
          },
        )

        if (active) setIsRenderingPreview(false)
      } catch (error) {
        if (!active) return
        setIsRenderingPreview(false)
        setPreviewError(
          `L’aperçu n’a pas pu être affiché. Le fichier DOCX reste téléchargeable. ${
            error?.message || ''
          }`.trim(),
        )
      }
    }

    renderPreview()
    return () => {
      active = false
    }
  }, [generatedDocument, previewDocument])

  const downloadDocument = (blob, filename) => {
    const href = URL.createObjectURL(blob)
    const link = window.document.createElement('a')
    link.href = href
    link.download = filename || 'document.docx'
    window.document.body.append(link)
    link.click()
    link.remove()
    window.setTimeout(() => URL.revokeObjectURL(href), 1000)
  }

  const handleGenerate = async () => {
    if (!objectId || !selectedTemplateId || isGenerating) return

    setGenerationError('')
    setGenerationSuccess('')
    setGeneratedDocument(null)
    setPreviewError('')
    setIsGenerating(true)

    try {
      const { blob, filename } = await apiDownload(
        `/document-templates/${selectedTemplateId}/generate/`,
        {
          method: 'POST',
          body: { object_id: Number(objectId) },
        },
      )
      if (previewDocument) {
        setGeneratedDocument({ blob, filename })
      } else {
        downloadDocument(blob, filename)
        setGenerationSuccess(`Le document ${objectLabel || ''} a été téléchargé.`.trim())
      }
    } catch (error) {
      setGenerationError(errorMessage(error))
    } finally {
      setIsGenerating(false)
    }
  }

  const handleDownload = () => {
    if (!generatedDocument) return
    downloadDocument(generatedDocument.blob, generatedDocument.filename)
  }

  const handlePrint = () => {
    if (isRenderingPreview || previewError) return
    const previewWindow = previewFrameRef.current?.contentWindow
    if (!previewWindow) {
      setPreviewError('La fenêtre de prévisualisation est indisponible.')
      return
    }
    previewWindow.focus()
    previewWindow.print()
  }

  return (
    <div className="form-shell" aria-label={title || 'Génération documentaire'}>
      <h4>{title || 'Générer un document DOCX'}</h4>
      {isLoadingTemplates ? (
        <p role="status">Chargement des modèles approuvés…</p>
      ) : templateError ? (
        <p className="error-text" role="alert">{templateError}</p>
      ) : templates.length === 0 ? (
        <p className="muted">Aucun modèle approuvé n’est disponible pour ce type de document.</p>
      ) : (
        <>
          <label>
            Modèle DOCX approuvé
            <select
              value={selectedTemplateId}
              onChange={(event) => {
                setSelectedTemplateId(event.target.value)
                setGenerationError('')
                setGenerationSuccess('')
                setGeneratedDocument(null)
                setPreviewError('')
              }}
              disabled={isGenerating}
            >
              <option value="">Sélectionner un modèle</option>
              {templates.map((template) => (
                <option key={template.id} value={template.id}>
                  {template.name}
                </option>
              ))}
            </select>
          </label>
          <button
            type="button"
            className="btn btn-primary btn-sm"
            onClick={handleGenerate}
            disabled={!objectId || !selectedTemplateId || isGenerating}
          >
            {isGenerating
              ? 'Génération…'
              : previewDocument
                ? 'Générer / Voir la facture'
                : 'Générer et télécharger'}
          </button>
        </>
      )}
      {!objectId && <p className="muted">Sélectionnez d’abord un document source.</p>}
      {generationError && <p className="error-text" role="alert">{generationError}</p>}
      {generationSuccess && <p className="success-text" role="status">{generationSuccess}</p>}
      {generatedDocument && previewDocument && (
        <div className="card" role="region" aria-label="Aperçu de la facture générée">
          <div className="dashboard-page-header">
            <div>
              <h5 style={{ margin: 0 }}>Facture générée — {objectLabel}</h5>
              <p className="muted" style={{ margin: '0.25rem 0 0' }}>
                Aperçu du fichier DOCX renvoyé par le serveur.
              </p>
            </div>
            <div className="table-actions">
              <button
                type="button"
                className="btn btn-outline btn-sm"
                onClick={handlePrint}
                disabled={isRenderingPreview || Boolean(previewError)}
              >
                Imprimer
              </button>
              <button
                type="button"
                className="btn btn-outline btn-sm"
                onClick={handleDownload}
              >
                Télécharger
              </button>
              <button
                type="button"
                className="btn btn-outline btn-sm"
                onClick={() => {
                  setGeneratedDocument(null)
                  setPreviewError('')
                }}
              >
                Fermer l’aperçu
              </button>
            </div>
          </div>
          {isRenderingPreview && (
            <p className="muted" role="status">Préparation de l’aperçu…</p>
          )}
          {previewError && <p className="error-text" role="alert">{previewError}</p>}
          <iframe
            ref={previewFrameRef}
            title={`Aperçu de la facture ${objectLabel || ''}`}
            style={{
              display: previewError ? 'none' : 'block',
              width: '100%',
              height: 'min(75vh, 900px)',
              minHeight: '480px',
              border: '1px solid var(--color-border)',
              borderRadius: 'var(--radius-md)',
              background: '#fff',
            }}
          />
        </div>
      )}
    </div>
  )
}

export default DynamicDocumentGenerator
