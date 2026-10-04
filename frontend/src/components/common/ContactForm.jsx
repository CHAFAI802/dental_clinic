import { useEffect, useMemo, useState } from 'react'
import { useSiteConfig } from '../../context/SiteConfigContext.jsx'
import { apiGet, apiPost } from '../../api/client.js'

const MONTH_LABELS = [
'Janvier',
'Février',
'Mars',
'Avril',
'Mai',
'Juin',
'Juillet',
'Août',
'Septembre',
'Octobre',
'Novembre',
'Décembre',
]

const CURRENT_YEAR = new Date().getFullYear()
const BIRTH_YEAR_MIN = 1900
// Plage courte et raisonnable pour une date de naissance (quelques années
// d'avenir tolérées pour couvrir tous les cas de saisie).
const BIRTH_YEAR_MAX = CURRENT_YEAR + 5

function isLeapYear(year) {
return (year % 4 === 0 && year % 100 !== 0) || year % 400 === 0
}

function getDaysInMonth(month, year) {
if (!month) return 31

const monthNumber = Number(month)

if (monthNumber === 2) {
return year && isLeapYear(Number(year)) ? 29 : 28
}

return [4, 6, 9, 11].includes(monthNumber) ? 30 : 31
}

function ContactForm({ title = 'Prendre rendez-vous' }) {
const { config } = useSiteConfig()
const contact = config.contact

const [slots, setSlots] = useState([])
const [loadingSlots, setLoadingSlots] = useState(true)
const [slotsError, setSlotsError] = useState(null)

const [form, setForm] = useState({
first_request: true,
patient_code: '',
first_name: '',
last_name: '',
email: '',
phone: '',
birth_day: '',
birth_month: '',
birth_year: '',
gender: '',
practitioner: '',
date: '',
slot: '',
reason: '',
})

const [status, setStatus] = useState(null)
const [submitting, setSubmitting] = useState(false)

useEffect(() => {
let cancelled = false

async function loadSlots() {
  setLoadingSlots(true)
  setSlotsError(null)

  try {
    const data = await apiGet('/appointment-slots/')

    if (!cancelled) {
      setSlots(Array.isArray(data) ? data : [])
    }
  } catch (error) {
    if (!cancelled) {
      setSlotsError(
        error.message || 'Impossible de charger les créneaux disponibles.',
      )
    }
  } finally {
    if (!cancelled) {
      setLoadingSlots(false)
    }
  }
}

loadSlots()

return () => {
  cancelled = true
}

}, [])

const practitioners = useMemo(() => {
const map = new Map()

slots.forEach((slot) => {
  if (!map.has(slot.practitioner)) {
    map.set(slot.practitioner, {
      id: slot.practitioner,
      name: slot.practitioner_name,
    })
  }
})

return Array.from(map.values())

}, [slots])

const availableDates = useMemo(() => {
const filtered = form.practitioner
? slots.filter(
(slot) => String(slot.practitioner) === String(form.practitioner),
)
: slots

return [...new Set(filtered.map((slot) => slot.date))]

}, [slots, form.practitioner])

const availableSlots = useMemo(() => {
return slots.filter((slot) => {
if (
form.practitioner &&
String(slot.practitioner) !== String(form.practitioner)
) {
return false
}

  if (form.date && slot.date !== form.date) {
    return false
  }

  return true
})

}, [slots, form.practitioner, form.date])

const birthYears = useMemo(() => {
const years = []

for (let year = BIRTH_YEAR_MAX; year >= BIRTH_YEAR_MIN; year -= 1) {
  years.push(String(year))
}

return years


}, [])

const birthDays = useMemo(() => {
const total = getDaysInMonth(form.birth_month, form.birth_year)

return Array.from({ length: total }, (_, index) =>
  String(index + 1).padStart(2, '0'),
)


}, [form.birth_month, form.birth_year])

const handleChange = (event) => {
const { name, value } = event.target

setStatus(null)

setForm((current) => {
  const next = {
    ...current,
    [name]: value,
  }

  if (name === 'practitioner') {
    next.date = ''
    next.slot = ''
  }

  if (name === 'date') {
    next.slot = ''
  }

  if (name === 'birth_month' || name === 'birth_year') {
    const month = name === 'birth_month' ? value : current.birth_month
    const year = name === 'birth_year' ? value : current.birth_year

    if (
      current.birth_day &&
      Number(current.birth_day) > getDaysInMonth(month, year)
    ) {
      next.birth_day = ''
    }
  }

  return next
})


}

const handleRequestTypeChange = (event) => {
const firstRequest = event.target.value === 'true'

setStatus(null)

setForm((current) => ({
  ...current,
  first_request: firstRequest,
  patient_code: firstRequest ? '' : current.patient_code,
  first_name: firstRequest ? current.first_name : '',
  last_name: firstRequest ? current.last_name : '',
  email: firstRequest ? current.email : '',
  phone: firstRequest ? current.phone : '',
  birth_day: firstRequest ? current.birth_day : '',
  birth_month: firstRequest ? current.birth_month : '',
  birth_year: firstRequest ? current.birth_year : '',
  gender: firstRequest ? current.gender : '',
}))

}

const formatDate = (date) => {
return new Intl.DateTimeFormat('fr-FR', {
weekday: 'long',
day: 'numeric',
month: 'long',
year: 'numeric',
}).format(new Date(`${date}T12:00:00`))
}

const formatTime = (dateTime) => {
return new Intl.DateTimeFormat('fr-FR', {
hour: '2-digit',
minute: '2-digit',
}).format(new Date(dateTime))
}

const buildBirthdate = () => {
if (!form.birth_day || !form.birth_month || !form.birth_year) {
return null
}

const day = Number(form.birth_day)
const month = Number(form.birth_month)
const year = Number(form.birth_year)

if (!day || !month || !year) return null
if (day > getDaysInMonth(form.birth_month, form.birth_year)) return null

const isoDate = `${year}-${String(month).padStart(2, '0')}-${String(
  day,
).padStart(2, '0')}`
const parsed = new Date(`${isoDate}T00:00:00`)

if (
  Number.isNaN(parsed.getTime()) ||
  parsed.getFullYear() !== year ||
  parsed.getMonth() + 1 !== month ||
  parsed.getDate() !== day
) {
  return null
}

return isoDate

}

const handleSubmit = async (event) => {
event.preventDefault()

setStatus(null)

const selectedSlot = slots.find(
  (slot) => String(slot.start_at) === String(form.slot),
)

if (!selectedSlot) {
  setStatus({
    type: 'error',
    message: 'Veuillez sélectionner un créneau disponible.',
  })
  return
}

if (!form.first_request && !form.patient_code.trim()) {
  setStatus({
    type: 'error',
    message: 'Veuillez saisir votre code patient.',
  })
  return
}

let birthdate = null

if (form.first_request) {
  birthdate = buildBirthdate()

  if (!birthdate) {
    setStatus({
      type: 'error',
      message:
        'Veuillez sélectionner une date de naissance complète et valide (jour, mois et année).',
    })
    return
  }

  if (form.gender !== 'M' && form.gender !== 'F') {
    setStatus({
      type: 'error',
      message:
        'Veuillez sélectionner Mâle ou Femelle pour le champ Genre.',
    })
    return
  }
}

setSubmitting(true)

try {
  const payload = {
    first_request: form.first_request,
    practitioner: selectedSlot.practitioner,
    start_at: selectedSlot.start_at,
    end_at: selectedSlot.end_at,
    reason: form.reason,
  }

  if (form.first_request) {
    payload.first_name = form.first_name
    payload.last_name = form.last_name
    payload.email = form.email
    payload.phone = form.phone
    payload.birthdate = birthdate
    payload.gender = form.gender
  } else {
    payload.patient_code = form.patient_code.trim()
  }

  const response = await apiPost('/appointment-request/', payload)

  setStatus({
    type: 'success',
    message:
      'Votre demande de rendez-vous a bien été envoyée. Le cabinet vous contactera pour sa confirmation.',
    patientCode: response?.patient_code || '',
  })

  setForm({
    first_request: true,
    patient_code: '',
    first_name: '',
    last_name: '',
    email: '',
    phone: '',
    birth_day: '',
    birth_month: '',
    birth_year: '',
    gender: '',
    practitioner: '',
    date: '',
    slot: '',
    reason: '',
  })
} catch (error) {
  setStatus({
    type: 'error',
    message:
      error.message ||
      'Impossible d’envoyer votre demande de rendez-vous.',
  })
} finally {
  setSubmitting(false)
}
}

return ( <form className="form-shell" onSubmit={handleSubmit}> <h3 className="card-title">{title}</h3>

  <div className="form-row">
    <div className="form-group">
      <label htmlFor="first_request">Vous êtes</label>
      <select
        id="first_request"
        name="first_request"
        value={String(form.first_request)}
        onChange={handleRequestTypeChange}
      >
        <option value="true">Nouveau patient</option>
        <option value="false">Patient déjà suivi au cabinet</option>
      </select>
    </div>

    {!form.first_request && (
      <div className="form-group">
        <label htmlFor="patient_code">Code patient</label>
        <input
          id="patient_code"
          name="patient_code"
          type="text"
          value={form.patient_code}
          onChange={handleChange}
          required={!form.first_request}
          autoComplete="off"
        />
      </div>
    )}
  </div>

  {form.first_request && (
    <>
      <div className="form-row">
        <div className="form-group">
          <label htmlFor="first_name">Prénom</label>
          <input
            id="first_name"
            name="first_name"
            type="text"
            value={form.first_name}
            onChange={handleChange}
            required
          />
        </div>

        <div className="form-group">
          <label htmlFor="last_name">Nom</label>
          <input
            id="last_name"
            name="last_name"
            type="text"
            value={form.last_name}
            onChange={handleChange}
            required
          />
        </div>
      </div>

      <div className="form-row">
        <div className="form-group">
          <label htmlFor="email">Email</label>
          <input
            id="email"
            name="email"
            type="email"
            value={form.email}
            onChange={handleChange}
            required
          />
        </div>

        <div className="form-group">
          <label htmlFor="phone">Téléphone</label>
          <input
            id="phone"
            name="phone"
            type="tel"
            value={form.phone}
            onChange={handleChange}
            required
          />
        </div>
      </div>

      <div className="form-group">
        <label>Date de naissance</label>
        <div className="birthdate-selects">
          <div className="form-group">
            <label htmlFor="birth_day">Jour</label>
            <select
              id="birth_day"
              name="birth_day"
              value={form.birth_day}
              onChange={handleChange}
              required
            >
              <option value="">Jour</option>

              {birthDays.map((day) => (
                <option key={day} value={day}>
                  {day}
                </option>
              ))}
            </select>
          </div>

          <div className="form-group">
            <label htmlFor="birth_month">Mois</label>
            <select
              id="birth_month"
              name="birth_month"
              value={form.birth_month}
              onChange={handleChange}
              required
            >
              <option value="">Mois</option>

              {MONTH_LABELS.map((label, index) => (
                <option key={label} value={String(index + 1)}>
                  {label}
                </option>
              ))}
            </select>
          </div>

          <div className="form-group">
            <label htmlFor="birth_year">Année</label>
            <select
              id="birth_year"
              name="birth_year"
              value={form.birth_year}
              onChange={handleChange}
              required
            >
              <option value="">Année</option>

              {birthYears.map((year) => (
                <option key={year} value={year}>
                  {year}
                </option>
              ))}
            </select>
          </div>
        </div>
      </div>

      <div className="form-row">
        <div className="form-group">
          <label htmlFor="gender">Genre</label>
          {/* Deux stricts choix : Mâle ou Femelle, rien d'autre.
              Sans option vide autorisée, le navigateur pré-sélectionnerait la
              première option : on force un état vide tant que l'utilisateur
              n'a pas fait son choix. */}
          <select
            id="gender"
            name="gender"
            value={form.gender}
            onChange={handleChange}
            required
            ref={(node) => {
              if (node && !form.gender) {
                node.selectedIndex = -1
              }
            }}
          >
            <option value="M">Mâle</option>
            <option value="F">Femelle</option>
          </select>
        </div>
      </div>
    </>
  )}

  <div className="form-row">
    <div className="form-group">
      <label htmlFor="practitioner">Dentiste</label>
      <select
        id="practitioner"
        name="practitioner"
        value={form.practitioner}
        onChange={handleChange}
        required
        disabled={loadingSlots || practitioners.length === 0}
      >
        <option value="">
          {loadingSlots
            ? 'Chargement des dentistes...'
            : 'Choisir un dentiste'}
        </option>

        {practitioners.map((practitioner) => (
          <option key={practitioner.id} value={practitioner.id}>
            {practitioner.name}
          </option>
        ))}
      </select>
    </div>

    <div className="form-group">
      <label htmlFor="date">Date</label>
      <select
        id="date"
        name="date"
        value={form.date}
        onChange={handleChange}
        required
        disabled={!form.practitioner || availableDates.length === 0}
      >
        <option value="">Choisir une date</option>

        {availableDates.map((date) => (
          <option key={date} value={date}>
            {formatDate(date)}
          </option>
        ))}
      </select>
    </div>
  </div>

  <div className="form-group">
    <label htmlFor="slot">Créneau</label>
    <select
      id="slot"
      name="slot"
      value={form.slot}
      onChange={handleChange}
      required
      disabled={!form.date || availableSlots.length === 0}
    >
      <option value="">Choisir une heure</option>

      {availableSlots.map((slot) => (
        <option key={slot.start_at} value={slot.start_at}>
          {formatTime(slot.start_at)} – {formatTime(slot.end_at)}
        </option>
      ))}
    </select>
  </div>

  <div className="form-group">
    <label htmlFor="reason">Motif de la demande</label>
    <textarea
      id="reason"
      name="reason"
      value={form.reason}
      onChange={handleChange}
      rows="4"
      placeholder="Indiquez brièvement le motif de votre demande."
    />
  </div>

  {loadingSlots && (
    <p className="contact-note">
      Chargement des créneaux disponibles…
    </p>
  )}

  {slotsError && (
    <p className="error-text">
      {slotsError}
    </p>
  )}

  {!loadingSlots && !slotsError && slots.length === 0 && (
    <p className="contact-note">
      Aucun créneau n’est actuellement disponible en ligne.
      Vous pouvez nous contacter directement au {contact.phone}.
    </p>
  )}

  <button
    type="submit"
    className="btn btn-accent"
    disabled={submitting || loadingSlots || slots.length === 0}
  >
    {submitting ? 'Envoi en cours…' : 'Envoyer la demande'}
  </button>

  {status && (
    <div
      className={
        status.type === 'success'
          ? 'success-text'
          : 'error-text'
      }
    >
      <p>{status.message}</p>

      {status.type === 'success' && status.patientCode && (
        <p>
          <strong>
            Votre code patient : {status.patientCode}. Conservez-le pour
            votre prochain accès.
          </strong>
        </p>
      )}
    </div>
  )}

  <p className="contact-note">
    Votre demande sera traitée par le cabinet. En cas d’urgence,
    appelez le {contact.phone}.
  </p>
</form>


)
}
export default ContactForm
