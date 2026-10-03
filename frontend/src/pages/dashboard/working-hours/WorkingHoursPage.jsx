import { useEffect, useMemo, useState } from 'react'

import { apiDelete, apiGet, apiPatch, apiPost } from '../../../api/client.js'
import Icon from '../../../components/common/Icon.jsx'
import { useAuth } from '../../../context/AuthContext.jsx'

/*
 * Backend : WorkingHoursViewSet (viewsets.ModelViewSet)
 *           permission_classes = [IsAdministrator]
 *           → super_admin, administrator sur toutes les actions
 *             (list, create, partial_update, destroy).
 *
 * Champs (WorkingHoursSerializer) :
 *   - practitioner      : obligatoire (clé étrangère vers User, rôle dentist)
 *   - weekday           : 0 = lundi … 6 = dimanche
 *   - start_time        : obligatoire (HH:MM:SS côté API)
 *   - end_time          : obligatoire, strictement > start_time (contrainte backend)
 *   - is_active         : booléen, défaut true
 *   - id, practitioner_name, weekday_display : lecture seule
 *
 * Un praticien peut avoir plusieurs plages par jour : la vue est donc
 * organisée par jour, avec autant de plages que renvoyées par l'API.
 * La liste des dentistes vient de /api/users/ (filtre rôle côté frontend) :
 * aucun endpoint n'est inventé.
 */

const WEEKDAYS = [
  { value: 0, label: 'Lundi' },
  { value: 1, label: 'Mardi' },
  { value: 2, label: 'Mercredi' },
  { value: 3, label: 'Jeudi' },
  { value: 4, label: 'Vendredi' },
  { value: 5, label: 'Samedi' },
  { value: 6, label: 'Dimanche' },
]

const ACTIVE_BADGE_STYLE = {
  background: 'var(--color-primary-soft)',
  color: 'var(--color-success)',
}

const INACTIVE_BADGE_STYLE = {
  background: 'var(--color-accent-soft)',
  color: 'var(--color-accent-hover)',
}

const styles = {
  title: { display: 'flex', alignItems: 'center', gap: '0.5rem' },
  noMargin: { margin: 0 },
  // Plus large que la grille par défaut, sans jamais déborder sur mobile.
  weekGrid: { gridTemplateColumns: 'repeat(auto-fill, minmax(min(320px, 100%), 1fr))' },
  dayHeader: {
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'space-between',
    gap: '0.5rem',
    marginBottom: 'var(--space-2)',
  },
  dayTitle: { margin: 0 },
  emptyDay: { margin: '0 0 var(--space-3)' },
  slotList: {
    listStyle: 'none',
    margin: '0 0 var(--space-3)',
    padding: 0,
    display: 'grid',
    gap: '0.5rem',
  },
  slotRow: {
    display: 'flex',
    flexWrap: 'wrap',
    alignItems: 'center',
    justifyContent: 'space-between',
    gap: '0.5rem',
    border: '1px solid var(--color-border)',
    borderRadius: 'var(--radius-md)',
    padding: '0.6rem 0.75rem',
  },
  slotFormRow: {
    display: 'flex',
    flexWrap: 'wrap',
    alignItems: 'flex-start',
    justifyContent: 'space-between',
    gap: '0.5rem',
    border: '1px solid var(--color-border)',
    borderRadius: 'var(--radius-md)',
    padding: '0.6rem 0.75rem',
  },
  slotTimes: {
    display: 'inline-flex',
    flexWrap: 'wrap',
    alignItems: 'center',
    gap: '0.4rem',
  },
  formBlock: { flex: '1 1 220px', minWidth: 0 },
  toggleBadge: { border: 'none', cursor: 'pointer', fontFamily: 'inherit' },
}

function badgeStyle(isActive) {
  return isActive ? ACTIVE_BADGE_STYLE : INACTIVE_BADGE_STYLE
}

// L'API renvoie HH:MM:SS, les champs <input type="time"> attendent HH:MM.
function formatTime(value) {
  if (!value) return '-'
  const text = String(value)
  return text.length >= 5 ? text.slice(0, 5) : text
}

function timeInputValue(value) {
  return formatTime(value) === '-' ? '' : formatTime(value)
}

function dentistLabel(user) {
  const name = [user?.first_name, user?.last_name].filter(Boolean).join(' ')
  return name || user?.email || `Utilisateur #${user?.id}`
}

function friendlyErrorMessage(err) {
  if (err?.status === 403) {
    return 'Accès refusé : votre rôle ne permet pas de gérer les horaires de travail.'
  }

  const message = err?.message

  if (!message || message === 'Failed to fetch') {
    return 'Une erreur est survenue. Veuillez réessayer.'
  }

  return message
}

function validateTimes({ start_time, end_time }) {
  if (!start_time || !end_time) {
    return 'Les heures de début et de fin sont obligatoires.'
  }

  if (end_time <= start_time) {
    return 'L’heure de fin doit être strictement supérieure à l’heure de début.'
  }

  return ''
}

function PageHeader() {
  return (
    <div className="dashboard-page-header">
      <div>
        <h2 style={styles.title}>
          <Icon name="clock" />
          Horaires de travail
        </h2>
        <p>Configurez les jours et plages horaires de disponibilité de chaque praticien.</p>
        <p>
          Source : <code>/api/working-hours/</code>
        </p>
      </div>
    </div>
  )
}

function WorkingHoursPage() {
  const { user: currentUser } = useAuth()

  const canManage = ['super_admin', 'administrator'].includes(currentUser?.role)

  const [users, setUsers] = useState([])
  const [usersError, setUsersError] = useState('')
  const [areUsersLoading, setAreUsersLoading] = useState(true)

  const [slots, setSlots] = useState([])
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState('')

  const [selectedId, setSelectedId] = useState(null)

  // Une seule ligne de formulaire ouverte à la fois :
  // mode "create" (nouvelle plage) ou mode "edit" (plage existante).
  const [form, setForm] = useState(null)
  const [formError, setFormError] = useState('')
  const [isSaving, setIsSaving] = useState(false)
  const [deletingId, setDeletingId] = useState(null)
  const [togglingId, setTogglingId] = useState(null)
  const [actionError, setActionError] = useState('')
  const [actionSuccess, setActionSuccess] = useState('')

  const loadUsers = async () => {
    setAreUsersLoading(true)
    setUsersError('')

    try {
      const data = await apiGet('/users/')
      setUsers(Array.isArray(data) ? data : [])
    } catch (err) {
      setUsersError(friendlyErrorMessage(err))
    } finally {
      setAreUsersLoading(false)
    }
  }

  const loadSlots = async () => {
    setIsLoading(true)
    setError('')

    try {
      const data = await apiGet('/working-hours/')
      setSlots(Array.isArray(data) ? data : [])
    } catch (err) {
      setError(friendlyErrorMessage(err))
    } finally {
      setIsLoading(false)
    }
  }

  useEffect(() => {
    if (!canManage) {
      setAreUsersLoading(false)
      setIsLoading(false)
      return
    }

    loadUsers()
    loadSlots()
    // Chargement initial de la page.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [canManage])

  const dentists = useMemo(
    () =>
      users
        .filter((u) => u.role === 'dentist')
        .sort((a, b) => dentistLabel(a).localeCompare(dentistLabel(b))),
    [users],
  )

  const slotsByWeekday = useMemo(() => {
    const grouped = new Map(WEEKDAYS.map((day) => [day.value, []]))

    if (selectedId !== null) {
      slots.forEach((slot) => {
        if (slot.practitioner === selectedId && grouped.has(slot.weekday)) {
          grouped.get(slot.weekday).push(slot)
        }
      })
    }

    grouped.forEach((list) => {
      list.sort((a, b) => String(a.start_time).localeCompare(String(b.start_time)))
    })

    return grouped
  }, [selectedId, slots])

  if (!canManage) {
    return (
      <section>
        <h2>Horaires de travail</h2>
        <p className="error-text">
          Accès refusé. Seuls le super admin et les administrateurs peuvent gérer les horaires de
          travail.
        </p>
      </section>
    )
  }

  if (isLoading || areUsersLoading) {
    return (
      <section>
        <PageHeader />
        <p>Chargement…</p>
      </section>
    )
  }

  const resetFeedback = () => {
    setActionError('')
    setActionSuccess('')
    setFormError('')
  }

  const handleSelectPractitioner = (event) => {
    const raw = event.target.value

    setSelectedId(raw === '' ? null : Number(raw))
    setForm(null)
    resetFeedback()
  }

  const startCreate = (weekday) => {
    resetFeedback()
    setForm({ mode: 'create', weekday, start_time: '08:00', end_time: '12:00', is_active: true })
  }

  const startEdit = (slot) => {
    resetFeedback()
    setForm({
      mode: 'edit',
      id: slot.id,
      weekday: slot.weekday,
      start_time: timeInputValue(slot.start_time),
      end_time: timeInputValue(slot.end_time),
      is_active: slot.is_active !== false,
    })
  }

  const cancelForm = () => {
    setForm(null)
    setFormError('')
  }

  const setFormField = (field, value) => {
    setFormError('')
    setForm((current) => (current ? { ...current, [field]: value } : current))
  }

  const handleSave = async () => {
    if (!form || selectedId === null || isSaving) return

    resetFeedback()

    const validationError = validateTimes(form)
    if (validationError) {
      setFormError(validationError)
      return
    }

    setIsSaving(true)

    try {
      if (form.mode === 'create') {
        const payload = {
          practitioner: selectedId,
          weekday: form.weekday,
          start_time: form.start_time,
          end_time: form.end_time,
          is_active: Boolean(form.is_active),
        }

        const created = await apiPost('/working-hours/', payload)
        setSlots((current) => [...current, created])
        setForm(null)
        setActionSuccess('Plage créée.')
      } else {
        const payload = {
          start_time: form.start_time,
          end_time: form.end_time,
          is_active: Boolean(form.is_active),
        }

        const updated = await apiPatch(`/working-hours/${form.id}/`, payload)
        setSlots((current) => current.map((slot) => (slot.id === updated.id ? updated : slot)))
        setForm(null)
        setActionSuccess('Plage mise à jour.')
      }
    } catch (err) {
      setFormError(friendlyErrorMessage(err))
    } finally {
      setIsSaving(false)
    }
  }

  const handleToggle = async (slot) => {
    if (togglingId !== null) return

    resetFeedback()
    setTogglingId(slot.id)

    try {
      const updated = await apiPatch(`/working-hours/${slot.id}/`, {
        is_active: !(slot.is_active !== false),
      })
      setSlots((current) => current.map((item) => (item.id === updated.id ? updated : item)))
      setActionSuccess(updated.is_active !== false ? 'Plage activée.' : 'Plage désactivée.')
    } catch (err) {
      setActionError(friendlyErrorMessage(err))
    } finally {
      setTogglingId(null)
    }
  }

  const handleDelete = async (slot) => {
    const confirmed = window.confirm(
      `Confirmer la suppression de la plage du ${formatTime(slot.start_time)} à ${formatTime(
        slot.end_time,
      )} ?`,
    )
    if (!confirmed) return

    resetFeedback()
    setDeletingId(slot.id)

    try {
      await apiDelete(`/working-hours/${slot.id}/`)
      setSlots((current) => current.filter((item) => item.id !== slot.id))

      if (form?.mode === 'edit' && form.id === slot.id) {
        setForm(null)
      }

      setActionSuccess('Plage supprimée.')
    } catch (err) {
      setActionError(friendlyErrorMessage(err))
    } finally {
      setDeletingId(null)
    }
  }

  const renderFormRow = (key) => (
    <li key={key} style={styles.slotFormRow}>
      <div className="form-shell" style={styles.formBlock}>
        <div className="form-row">
          <label>
            Début
            <input
              type="time"
              value={form.start_time}
              onChange={(event) => setFormField('start_time', event.target.value)}
            />
          </label>

          <label>
            Fin
            <input
              type="time"
              value={form.end_time}
              onChange={(event) => setFormField('end_time', event.target.value)}
            />
          </label>

          <label className="checkbox-row">
            <input
              type="checkbox"
              checked={form.is_active}
              onChange={(event) => setFormField('is_active', event.target.checked)}
            />
            Plage active
          </label>
        </div>

        {formError && (
          <p className="error-text" style={styles.noMargin}>
            {formError}
          </p>
        )}
      </div>

      <div className="table-actions">
        <button
          type="button"
          className="btn btn-primary btn-sm"
          onClick={handleSave}
          disabled={isSaving}
        >
          {isSaving ? 'Enregistrement…' : 'Enregistrer'}
        </button>

        <button
          type="button"
          className="btn btn-outline btn-sm"
          onClick={cancelForm}
          disabled={isSaving}
        >
          Annuler
        </button>
      </div>
    </li>
  )

  return (
    <section>
      <PageHeader />

      {actionError && <p className="error-text">{actionError}</p>}
      {actionSuccess && <p className="success-text">{actionSuccess}</p>}

      <div className="card" style={{ marginBottom: 'var(--space-5)' }}>
        <div className="form-shell">
          <label>
            Dentiste
            <select
              value={selectedId === null ? '' : String(selectedId)}
              onChange={handleSelectPractitioner}
              disabled={dentists.length === 0}
            >
              <option value="">
                {dentists.length === 0 ? 'Aucun dentiste disponible' : 'Sélectionner un dentiste'}
              </option>
              {dentists.map((dentist) => (
                <option key={dentist.id} value={dentist.id}>
                  {dentistLabel(dentist)}
                  {dentist.is_active === false ? ' (inactif)' : ''}
                </option>
              ))}
            </select>
          </label>
        </div>

        {usersError && (
          <p className="error-text" style={styles.noMargin}>
            {usersError}
          </p>
        )}
      </div>

      {error ? (
        <p className="error-text">{error}</p>
      ) : selectedId === null ? (
        <p className="muted">Sélectionnez un dentiste pour afficher ses horaires.</p>
      ) : (
        <div className="dashboard-grid" style={styles.weekGrid}>
          {WEEKDAYS.map((day) => {
            const daySlots = slotsByWeekday.get(day.value) || []
            const isCreateOpen = form?.mode === 'create' && form.weekday === day.value
            const dayIsActive = daySlots.some((slot) => slot.is_active !== false)

            return (
              <article className="dashboard-card" key={day.value}>
                <div style={styles.dayHeader}>
                  <h3 style={styles.dayTitle}>{day.label}</h3>
                  <span className="badge" style={badgeStyle(dayIsActive)}>
                    {dayIsActive ? 'Actif' : 'Inactif'}
                  </span>
                </div>

                {daySlots.length === 0 && !isCreateOpen ? (
                  <p className="muted" style={styles.emptyDay}>
                    Aucune plage configurée
                  </p>
                ) : (
                  <ul style={styles.slotList}>
                    {daySlots.map((slot) =>
                      form?.mode === 'edit' && form.id === slot.id ? (
                        renderFormRow(`edit-${slot.id}`)
                      ) : (
                        <li key={slot.id} style={styles.slotRow}>
                          <span style={styles.slotTimes}>
                            <strong>{formatTime(slot.start_time)}</strong>
                            <span aria-hidden="true">→</span>
                            <strong>{formatTime(slot.end_time)}</strong>
                            <button
                              type="button"
                              className="badge"
                              style={{ ...badgeStyle(slot.is_active !== false), ...styles.toggleBadge }}
                              onClick={() => handleToggle(slot)}
                              disabled={togglingId === slot.id}
                              title={
                                slot.is_active !== false
                                  ? 'Désactiver cette plage'
                                  : 'Activer cette plage'
                              }
                            >
                              {slot.is_active !== false ? 'Actif' : 'Inactif'}
                            </button>
                          </span>

                          <span className="table-actions">
                            <button
                              type="button"
                              className="btn btn-outline btn-sm"
                              onClick={() => startEdit(slot)}
                              disabled={isSaving}
                            >
                              Modifier
                            </button>
                            <button
                              type="button"
                              className="danger-link"
                              onClick={() => handleDelete(slot)}
                              disabled={deletingId === slot.id}
                            >
                              {deletingId === slot.id ? 'Suppression…' : 'Supprimer'}
                            </button>
                          </span>
                        </li>
                      ),
                    )}

                    {isCreateOpen && renderFormRow('create')}
                  </ul>
                )}

                {!isCreateOpen && (
                  <button
                    type="button"
                    className="btn btn-outline btn-sm btn-block"
                    onClick={() => startCreate(day.value)}
                    disabled={isSaving}
                  >
                    + Ajouter une plage
                  </button>
                )}
              </article>
            )
          })}
        </div>
      )}
    </section>
  )
}

export default WorkingHoursPage
