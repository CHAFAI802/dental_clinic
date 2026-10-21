/*
 * Utilitaires du module Documents (modèles Word).
 *
 * Toutes les valeurs affichées proviennent de l'API : seuls le formatage
 * des dates, des tailles et des URL de fichiers sont réalisés ici.
 */

export function formatDateTime(value) {
  if (!value) return '-'

  const date = new Date(value)
  if (Number.isNaN(date.getTime())) return String(value)

  return date.toLocaleString('fr-FR', {
    day: '2-digit',
    month: '2-digit',
    year: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  })
}

export function formatFileSize(bytes) {
  if (typeof bytes !== 'number' || !Number.isFinite(bytes) || bytes < 0) return ''

  if (bytes < 1024) return `${bytes} o`

  const units = ['Ko', 'Mo', 'Go']
  let value = bytes / 1024
  let index = 0

  while (value >= 1024 && index < units.length - 1) {
    value /= 1024
    index += 1
  }

  return `${value.toLocaleString('fr-FR', { maximumFractionDigits: 1 })} ${units[index]}`
}

/*
 * Badge « actif / inactif » : repris du champ is_active exposé par
 * DocumentTemplateSerializer.
 */
export function activeBadge(isActive) {
  return isActive
    ? {
        label: 'Actif',
        style: { background: 'var(--color-primary-soft)', color: 'var(--color-success)' },
      }
    : {
        label: 'Inactif',
        style: { background: 'var(--color-accent-soft)', color: 'var(--color-accent-hover)' },
      }
}

/*
 * L'API renvoie l'URL absolue du fichier construite avec l'hôte de la
 * requête reçue par Django (via le proxy Vite : http://web:8000/media/…).
 * Ce hôte n'est pas résoluble depuis le navigateur. Le frontend consomme
 * les ressources en même origine (convention : API_BASE_URL = '/api'),
 * on conserve donc uniquement le chemin retourné par le backend :
 * aucune donnée de stockage n'est codée en dur, seule l'origine est
 * retirée pour passer par le proxy de développement.
 */
export function mediaFileUrl(rawUrl) {
  if (!rawUrl) return null

  try {
    const url = new URL(rawUrl, window.location.origin)
    return `${url.pathname}${url.search}`
  } catch {
    return rawUrl
  }
}

/*
 * Message global exploitable (session expirée, accès refusé, réseau,
 * serveur) à partir de l'erreur levée par api/client.js.
 */
export function requestErrorMessage(error, fallback = 'La requête a échoué.') {
  if (error?.status === 401) {
    return 'Session expirée ou authentification invalide. Connectez-vous à nouveau.'
  }

  if (error?.status === 403) {
    return 'Accès refusé : la gestion des modèles de documents exige le rôle administrateur.'
  }

  if (typeof error?.status === 'number' && error.status >= 500) {
    return `Erreur serveur (${error.status}). Le détail est disponible dans les journaux du backend.`
  }

  if (!error?.status && !error?.data) {
    return 'Erreur réseau : le serveur est injoignable (vérifiez votre connexion).'
  }

  const message = typeof error?.message === 'string' ? error.message.trim() : ''

  if (!message) return fallback
  if (message.startsWith('<')) return `Erreur serveur (${error.status}).`

  return message
}

const TEMPLATE_FIELDS = new Set(['name', 'description', 'file', 'is_active'])

/*
 * Sépare les erreurs de validation DRF par champ (affichées sous le champ
 * concerné) des messages globaux. Les messages exacts du backend sont
 * conservés : aucun message précis n'est remplacé par un texte générique.
 */
export function splitApiErrors(error) {
  const fields = {}
  const messages = []

  // Session expirée / accès refusé : message prioritaire, lisible.
  if (error?.status === 401 || error?.status === 403) {
    return { fields, general: requestErrorMessage(error) }
  }

  const data = error?.data

  if (typeof data === 'string' && data.trim()) {
    const text = data.trim()
    messages.push(text.startsWith('<') ? `Erreur serveur (${error.status}).` : text)
  } else if (data && typeof data === 'object') {
    for (const [key, value] of Object.entries(data)) {
      const list = Array.isArray(value) ? value.map(String) : [String(value)]

      if (TEMPLATE_FIELDS.has(key)) {
        fields[key] = list.join('\n')
      } else if (key === 'detail' || key === 'non_field_errors') {
        messages.push(list.join(' '))
      } else {
        messages.push(list.map((line) => `${key} : ${line}`).join('\n'))
      }
    }
  }

  if (messages.length === 0) {
    const fallback = requestErrorMessage(error)
    if (fallback) messages.push(fallback)
  }

  return { fields, general: messages.join('\n') }
}
