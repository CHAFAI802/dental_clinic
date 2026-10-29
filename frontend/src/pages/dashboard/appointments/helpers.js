/*
 * Helpers du module Rendez-vous (frontend uniquement).
 *
 * Conventions du projet :
 *   - statuts réels renvoyés par l'API : pending, confirmed, completed,
 *     cancelled, no_show (valeurs minuscules du modèle Appointment) ;
 *   - dates au format ISO 8601 avec fuseau (USE_TZ, Europe/Paris),
 *     comparées en instants absolus via Date.parse.
 *
 * Aucune règle métier n'est recréée ici : ces fonctions ne font que
 * formater/dériver les champs déjà fournis par l'API (status, start_at,
 * end_at) pour l'affichage.
 */

/** Nombre de rendez-vous affichés par page de la liste. */
export const APPOINTMENTS_PAGE_SIZE = 10

/**
 * Teinte d'affichage d'un rendez-vous.
 *
 *   - 'completed' : statut COMPLETED → fond vert ;
 *   - 'missed'    : statut CONFIRMED et end_at antérieur ou égal à
 *                   maintenant → fond rouge (rendez-vous raté) ;
 *   - null        : tout le reste (confirmed à venir, pending, cancelled,
 *                   no_show, date illisible) → présentation inchangée.
 *
 * La comparaison porte sur end_at (jamais start_at) : un rendez-vous
 * confirmé commencé mais dont l'heure de fin n'est pas encore atteinte
 * n'est pas raté.
 */
export function getAppointmentTone(appointment, now = Date.now()) {
  if (!appointment) return null

  if (appointment.status === 'completed') return 'completed'

  if (appointment.status === 'confirmed') {
    const endAt = Date.parse(appointment.end_at ?? '')
    if (Number.isFinite(endAt) && endAt <= now) return 'missed'
  }

  return null
}

/** Classe CSS de la ligne de tableau selon la teinte du rendez-vous. */
export function getAppointmentToneClass(appointment, now = Date.now()) {
  const tone = getAppointmentTone(appointment, now)
  return tone ? `appointment-row is-${tone}` : 'appointment-row'
}

function toTimestamp(value) {
  const timestamp = Date.parse(value ?? '')
  // Date illisible → traitée comme « la plus ancienne » (fin de liste).
  return Number.isFinite(timestamp) ? timestamp : Number.NEGATIVE_INFINITY
}

/**
 * Tri décroissant par date/heure de début : les rendez-vous les plus
 * récents d'abord. Le décalage horaire ISO 8601 est pris en compte par
 * Date.parse, donc plusieurs rendez-vous le même jour sont ordonnés par
 * heure locale réelle. Égalité exacte → id décroissant (tri stable, sans
 * doublon ni perte).
 */
export function sortAppointmentsDesc(appointments) {
  return [...appointments].sort((a, b) => {
    const startA = toTimestamp(a?.start_at)
    const startB = toTimestamp(b?.start_at)

    if (startA !== startB) return startB - startA

    return Number(b?.id ?? 0) - Number(a?.id ?? 0)
  })
}

/**
 * Pagination frontend (l'API /appointments/ renvoie un tableau non
 * paginé). Renvoie la page demandée, recadrée dans les bornes :
 * liste vide → 1 page vide, jamais d'indice hors bornes.
 */
export function paginateAppointments(items, page, pageSize = APPOINTMENTS_PAGE_SIZE) {
  const size = pageSize > 0 ? pageSize : APPOINTMENTS_PAGE_SIZE
  const totalPages = Math.max(1, Math.ceil(items.length / size))
  const currentPage = Math.min(Math.max(1, Number(page) || 1), totalPages)
  const startIndex = (currentPage - 1) * size

  return {
    items: items.slice(startIndex, startIndex + size),
    currentPage,
    totalPages,
  }
}
