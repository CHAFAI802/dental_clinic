import { useEffect, useState } from 'react'

import { apiGet, apiPatch, apiPost } from '../../../api/client.js'
import {
  formatDateTime,
  mediaFileUrl,
  splitApiErrors,
} from '../documents/helpers.js'

/*
 * Section « Ordonnance » du dossier du médecin (DentistPatientPage).
 *
 * Contrat API respecté à la lettre (aucun champ inventé) :
 *
 *   GET  /api/document-templates/            → modèles ACTIFS et APPROUVÉS
 *                                              (filtre backend pour un dentiste)
 *   GET  /api/medications/?patient=<id>      → traitements déjà enregistrés
 *   POST /api/medications/?patient=<id>      → {name, dosage, frequency, route,
 *                                                start_date, end_date, notes}
 *                                              patient + prescribed_by fixés
 *                                              par le serveur
 *   PATCH /api/medications/<id>/             → mise à jour d'une ligne déjà
 *                                              enregistrée (évite les doublons)
 *   POST /api/prescriptions/generate-from-document-template/
 *        {patient, document_template, medications:[ids], notes}
 *                                              → 201 + generated_file (le
 *                                              VRAI fichier DOCX du backend)
 *
 * Le document n'est jamais reconstruit en HTML : ouverture, téléchargement
 * et impression pointent tous vers l'URL retournée par l'API.
 */

// Champs réellement exigés par MedicationSerializer (modèle sans blank=True).
const REQUIRED_LINE_FIELDS = [
  { key: 'name', label: 'Médicament' },
  { key: 'dosage', label: 'Dosage' },
  { key: 'frequency', label: 'Fréquence' },
  { key: 'route', label: 'Voie' },
  { key: 'start_date', label: 'Début' },
]

const LINE_FIELD_LABELS = {
  name: 'Médicament',
  dosage: 'Dosage',
  frequency: 'Fréquence',
  route: 'Voie',
  start_date: 'Début',
  end_date: 'Fin',
  notes: 'Notes',
}

function emptyLine() {
  return {
    id: null,
    name: '',
    dosage: '',
    frequency: '',
    route: '',
    start_date: '',
    end_date: '',
    notes: '',
    dirty: false,
  }
}

function linePayload(line) {
  return {
    name: String(line.name).trim(),
    dosage: String(line.dosage).trim(),
    frequency: String(line.frequency).trim(),
    route: String(line.route).trim(),
    start_date: line.start_date,
    end_date: line.end_date || null,
    notes: String(line.notes).trim(),
  }
}

function validateLines(lines) {
  const errors = {}

  lines.forEach((line, index) => {
    const fieldErrors = {}

    REQUIRED_LINE_FIELDS.forEach(({ key, label }) => {
      if (!String(line[key] ?? '').trim()) {
        fieldErrors[key] = `${label} est requis.`
      }
    })

    if (line.start_date && line.end_date && line.end_date < line.start_date) {
      fieldErrors.end_date = 'La date de fin est antérieure à la date de début.'
    }

    if (Object.keys(fieldErrors).length > 0) {
      errors[index] = fieldErrors
    }
  })

  return errors
}

function PrescriptionSection({ patientId, patient }) {
  const [templates, setTemplates] = useState([])
  const [areTemplatesLoading, setAreTemplatesLoading] = useState(true)
  const [templatesError, setTemplatesError] = useState('')
  const [templateId, setTemplateId] = useState('')

  const [notes, setNotes] = useState('')
  const [lines, setLines] = useState([emptyLine()])
  const [lineErrors, setLineErrors] = useState({})

  const [existingMedications, setExistingMedications] = useState([])
  const [areMedicationsLoading, setAreMedicationsLoading] = useState(true)
  const [medicationsError, setMedicationsError] = useState('')

  const [isGenerating, setIsGenerating] = useState(false)
  const [generateError, setGenerateError] = useState('')
  const [generated, setGenerated] = useState(null)

  // Modèles approuvés disponibles pour ce dentiste.
  useEffect(() => {
    let isMounted = true

    const run = async () => {
      setAreTemplatesLoading(true)
      setTemplatesError('')

      try {
        const data = await apiGet('/document-templates/')
        if (!isMounted) return
        const list = Array.isArray(data) ? data : []
        setTemplates(list)
        setTemplateId((current) => {
          if (current && list.some((item) => String(item.id) === current)) {
            return current
          }
          return list.length === 1 ? String(list[0].id) : ''
        })
      } catch (err) {
        if (!isMounted) return
        setTemplates([])
        setTemplatesError(splitApiErrors(err).general)
      } finally {
        if (isMounted) setAreTemplatesLoading(false)
      }
    }

    run()

    return () => {
      isMounted = false
    }
  }, [])

  // Traitements déjà enregistrés pour le patient ouvert.
  useEffect(() => {
    if (!patientId) {
      setExistingMedications([])
      setAreMedicationsLoading(false)
      return undefined
    }

    let isMounted = true

    const run = async () => {
      setAreMedicationsLoading(true)
      setMedicationsError('')

      try {
        const data = await apiGet(
          `/medications/?patient=${encodeURIComponent(patientId)}`,
        )
        if (isMounted) {
          setExistingMedications(Array.isArray(data) ? data : [])
        }
      } catch (err) {
        if (!isMounted) return
        setExistingMedications([])
        setMedicationsError(splitApiErrors(err).general)
      } finally {
        if (isMounted) setAreMedicationsLoading(false)
      }
    }

    run()

    return () => {
      isMounted = false
    }
  }, [patientId])

  const updateLine = (index, field, value) => {
    setLines((current) =>
      current.map((line, position) =>
        position === index
          ? { ...line, [field]: value, dirty: line.id !== null }
          : line,
      ),
    )
    setLineErrors((current) => {
      if (!current[index]) return current
      const next = { ...current[index] }
      delete next[field]
      return { ...current, [index]: next }
    })
  }

  const addLine = () => {
    setLines((current) => [...current, emptyLine()])
  }

  const removeLine = (index) => {
    // Suppression locale uniquement : un traitement déjà enregistré au
    // dossier patient n'est jamais détruit depuis ce formulaire.
    setLines((current) => current.filter((_, position) => position !== index))
    setLineErrors((current) => {
      const next = { ...current }
      delete next[index]
      return next
    })
  }

  const handleGenerate = async (event) => {
    event.preventDefault()
    setGenerateError('')

    const errors = validateLines(lines)
    setLineErrors(errors)
    if (Object.keys(errors).length > 0) return

    if (!templateId) {
      setGenerateError("Sélectionnez un modèle d'ordonnance.")
      return
    }

    if (lines.length === 0) {
      setGenerateError('Ajoutez au moins un médicament au traitement.')
      return
    }

    setIsGenerating(true)

    try {
      // 1. Enregistrement des lignes (création OU mise à jour) : le
      //    contrat de génération attend des identifiants de médicaments
      //    existants, appartenant au patient et prescrits par ce dentiste.
      const medicationIds = []

      for (const line of lines) {
        const payload = linePayload(line)
        let saved

        if (line.id && line.dirty) {
          saved = await apiPatch(`/medications/${line.id}/`, payload)
        } else if (line.id) {
          saved = line
        } else {
          saved = await apiPost(
            `/medications/?patient=${encodeURIComponent(patientId)}`,
            payload,
          )
        }

        medicationIds.push(saved.id)
      }

      setLines((current) =>
        current.map((line, index) => ({
          ...line,
          id: medicationIds[index],
          dirty: false,
        })),
      )

      // 2. Génération du VRAI document Word côté backend.
      const prescription = await apiPost(
        '/prescriptions/generate-from-document-template/',
        {
          patient: Number(patientId),
          document_template: Number(templateId),
          medications: medicationIds,
          notes,
        },
      )

      const fileUrl = mediaFileUrl(prescription?.generated_file)
      const fileName = fileUrl
        ? decodeURIComponent(fileUrl.split('/').pop() || '').split('?')[0]
        : ''

      setGenerated({
        id: prescription?.id,
        generatedAt: prescription?.generated_at,
        count: prescription?.filled_data?.medications?.length ?? medicationIds.length,
        fileUrl,
        fileName,
      })

      // Actualisation de la liste des traitements du dossier.
      try {
        const records = await apiGet(
          `/medications/?patient=${encodeURIComponent(patientId)}`,
        )
        setExistingMedications(Array.isArray(records) ? records : [])
        setMedicationsError('')
      } catch (err) {
        setMedicationsError(splitApiErrors(err).general)
      }
    } catch (err) {
      // Aucune simulation de succès : seul le message du backend est affiché.
      setGenerated(null)
      setGenerateError(splitApiErrors(err).general)
    } finally {
      setIsGenerating(false)
    }
  }

  const handleOpenDocument = () => {
    if (generated?.fileUrl) {
      window.open(generated.fileUrl, '_blank', 'noopener')
    }
  }

  const patientName =
    [patient?.first_name, patient?.last_name].filter(Boolean).join(' ') ||
    (patient?.id ? `Patient #${patient.id}` : '')

  const hasTemplates = templates.length > 0
  const canGenerate =
    !isGenerating && !areTemplatesLoading && hasTemplates && lines.length > 0

  return (
    <>
      <hr className="divider" />

      <h4>Ordonnance (document Word)</h4>
      <p className="muted" style={{ marginTop: 0 }}>
        Patient : <strong>{patientName}</strong> — les informations du patient
        proviennent du dossier, aucune ressaisie n'est nécessaire.
      </p>

      <form
        className="form-shell patient-record-form"
        data-testid="prescription-form"
        onSubmit={handleGenerate}
      >
        <label>
          Modèle d'ordonnance
          <select
            required
            data-testid="template-select"
            disabled={areTemplatesLoading || !hasTemplates}
            value={templateId}
            onChange={(event) => setTemplateId(event.target.value)}
          >
            <option value="">
              {areTemplatesLoading
                ? 'Chargement des modèles…'
                : templatesError
                  ? 'Modèles indisponibles'
                  : !hasTemplates
                    ? 'Aucun modèle approuvé disponible'
                    : 'Sélectionner un modèle'}
            </option>
            {templates.map((template) => (
              <option key={template.id} value={template.id}>
                {template.name}
              </option>
            ))}
          </select>
        </label>

        {areTemplatesLoading ? (
          <p className="muted" role="status">
            Chargement des modèles d'ordonnance…
          </p>
        ) : templatesError ? (
          <p className="error-text">{templatesError}</p>
        ) : !hasTemplates ? (
          <p className="muted" role="status">
            Aucun modèle d'ordonnance actif et approuvé n'est disponible pour
            votre compte. Contactez l'administrateur : un modèle Word doit être
            approuvé avant toute génération.
          </p>
        ) : null}

        <label>
          Notes de l'ordonnance (facultatif)
          <textarea
            rows={2}
            value={notes}
            onChange={(event) => setNotes(event.target.value)}
          />
        </label>

        <h6>Traitement médicamenteux</h6>

        {areMedicationsLoading ? (
          <p className="muted" role="status">
            Chargement des traitements du patient…
          </p>
        ) : medicationsError ? (
          <p className="error-text">{medicationsError}</p>
        ) : existingMedications.length > 0 ? (
          <p className="muted">
            Déjà enregistré au dossier :{' '}
            {existingMedications
              .map((item) =>
                [item.name, item.dosage].filter(Boolean).join(' — '),
              )
              .join(' · ')}
          </p>
        ) : null}

        {lines.length === 0 && (
          <p className="muted">
            Aucun médicament saisi : ajoutez au moins une ligne pour pouvoir
            générer l'ordonnance.
          </p>
        )}

        {lines.map((line, index) => {
          const errors = lineErrors[index] || {}

          return (
            <div
              key={index}
              className="card"
              data-testid="medication-line"
              style={{ marginBottom: 'var(--space-4)' }}
            >
              <div className="dashboard-page-header">
                <div>
                  <h6 style={{ margin: 0 }}>
                    Médicament {index + 1}
                    {line.id ? ' — enregistré' : ' — à enregistrer'}
                  </h6>
                </div>
                <div className="table-actions">
                  <button
                    type="button"
                    className="btn btn-outline btn-sm"
                    onClick={() => removeLine(index)}
                    disabled={isGenerating}
                  >
                    Retirer
                  </button>
                </div>
              </div>

              <div className="form-row">
                <label>
                  {LINE_FIELD_LABELS.name}
                  <input
                    required
                    value={line.name}
                    onChange={(event) => updateLine(index, 'name', event.target.value)}
                  />
                  {errors.name && <span className="error-text">{errors.name}</span>}
                </label>
                <label>
                  {LINE_FIELD_LABELS.dosage}
                  <input
                    required
                    value={line.dosage}
                    onChange={(event) => updateLine(index, 'dosage', event.target.value)}
                  />
                  {errors.dosage && <span className="error-text">{errors.dosage}</span>}
                </label>
              </div>

              <div className="form-row">
                <label>
                  {LINE_FIELD_LABELS.frequency}
                  <input
                    required
                    value={line.frequency}
                    onChange={(event) => updateLine(index, 'frequency', event.target.value)}
                  />
                  {errors.frequency && (
                    <span className="error-text">{errors.frequency}</span>
                  )}
                </label>
                <label>
                  {LINE_FIELD_LABELS.route}
                  <input
                    required
                    value={line.route}
                    onChange={(event) => updateLine(index, 'route', event.target.value)}
                  />
                  {errors.route && <span className="error-text">{errors.route}</span>}
                </label>
              </div>

              <div className="form-row">
                <label>
                  {LINE_FIELD_LABELS.start_date}
                  <input
                    required
                    type="date"
                    value={line.start_date}
                    onChange={(event) =>
                      updateLine(index, 'start_date', event.target.value)
                    }
                  />
                  {errors.start_date && (
                    <span className="error-text">{errors.start_date}</span>
                  )}
                </label>
                <label>
                  {LINE_FIELD_LABELS.end_date} (facultatif)
                  <input
                    type="date"
                    value={line.end_date}
                    onChange={(event) =>
                      updateLine(index, 'end_date', event.target.value)
                    }
                  />
                  {errors.end_date && (
                    <span className="error-text">{errors.end_date}</span>
                  )}
                </label>
              </div>

              <label>
                {LINE_FIELD_LABELS.notes} (facultatif)
                <textarea
                  rows={2}
                  value={line.notes}
                  onChange={(event) => updateLine(index, 'notes', event.target.value)}
                />
              </label>
            </div>
          )
        })}

        <div className="table-actions">
          <button
            type="button"
            className="btn btn-outline btn-sm"
            data-testid="add-medication"
            onClick={addLine}
            disabled={isGenerating}
          >
            + Ajouter un médicament
          </button>
        </div>

        {generateError && (
          <p className="error-text" role="alert" data-testid="generate-error">
            {generateError}
          </p>
        )}

        <button
          type="submit"
          data-testid="generate-prescription"
          disabled={!canGenerate}
        >
          {isGenerating ? 'Génération…' : "Générer l'ordonnance"}
        </button>
        {areTemplatesLoading && (
          <p className="muted" role="status">
            Chargement…
          </p>
        )}
        {!areTemplatesLoading && !hasTemplates && !templatesError && (
          <p className="muted">
            Génération impossible : aucun modèle approuvé n'est disponible.
          </p>
        )}
      </form>

      {generated && (
        <div
          className="card"
          role="status"
          aria-live="polite"
          data-testid="prescription-result"
        >
          <div className="dashboard-page-header">
            <div>
              <h5 style={{ margin: 0 }}>Ordonnance générée</h5>
              <p className="muted" style={{ margin: '0.25rem 0 0' }}>
                Prescription n° {generated.id ?? '-'} ·{' '}
                {generated.count ?? lines.length} médicament
                {(generated.count ?? lines.length) > 1 ? 's' : ''} ·{' '}
                {formatDateTime(generated.generatedAt)}
              </p>
            </div>
          </div>

          <p className="success-text">
            Document Word généré par le backend à partir du modèle approuvé.
          </p>

          <div className="table-actions">
            <button
              type="button"
              className="btn btn-sm"
              data-testid="open-document"
              onClick={handleOpenDocument}
            >
              Ouvrir le document
            </button>

            {generated.fileUrl && (
              <a
                className="btn btn-outline btn-sm"
                data-testid="download-document"
                href={generated.fileUrl}
                download={generated.fileName || undefined}
              >
                Télécharger
              </a>
            )}

            <button
              type="button"
              className="btn btn-outline btn-sm"
              data-testid="print-document"
              onClick={handleOpenDocument}
              disabled={!generated.fileUrl}
            >
              Imprimer
            </button>
          </div>

          <p className="muted" style={{ marginBottom: 0 }}>
            Le fichier imprimé est celui renvoyé par le backend (
            {generated.fileName || 'fichier DOCX'}) : il s'ouvre dans
            Word/LibreOffice, qui conserve l'en-tête, les marges, la signature
            et la pagination du modèle.
          </p>
        </div>
      )}
    </>
  )
}

export default PrescriptionSection
