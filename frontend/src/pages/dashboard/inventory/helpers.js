/*
 * Utilitaires du module Inventaire.
 *
 * Le formatage et la gestion d'erreurs sont hérités des utilitaires déjà
 * utilisés par les modules Billing et Documents : aucune duplication et
 * aucun nouveau mécanisme. Les valeurs affichées proviennent exclusivement
 * des API backend.
 */

import { formatAmount, formatDate } from '../billing/helpers.js'
import {
  activeBadge,
  formatDateTime,
  requestErrorMessage,
  splitApiErrors,
} from '../documents/helpers.js'

export {
  activeBadge,
  formatAmount,
  formatDate,
  formatDateTime,
  requestErrorMessage,
  splitApiErrors,
}

/*
 * Rôles autorisés par les permissions backend (accounts/permissions.py) :
 *   IsAdministrator → inventaire-categories, familles, unités, fournisseurs
 *   CanManageStock  → articles, entrées, sorties, alertes, allocations,
 *                     destructions
 *
 * Ces jeux de rôles servent uniquement à masquer les actions inaccessibles :
 * le backend reste responsable de l'application des permissions.
 */
const CATALOG_ROLES = new Set(['super_admin', 'administrator'])
const STOCK_ROLES = new Set([
  'super_admin',
  'administrator',
  'accountant',
  'receptionist',
])

export function canManageCatalog(role) {
  return CATALOG_ROLES.has(role)
}

export function canManageStock(role) {
  return STOCK_ROLES.has(role)
}

/* Libellés repris des choix exposés par les modèles inventory/models.py. */
export const ALERT_TYPE_LABELS = {
  low_stock: 'Stock insuffisant',
  expiration: 'Péremption',
}

export const DESTRUCTION_STATUS_LABELS = {
  recorded: 'Enregistrée',
  completed: 'Destruction effectuée',
}

export const SELECTION_MODE_LABELS = {
  automatic: 'Automatique',
  manual: 'Manuel',
}

export function alertBadge(alertType) {
  if (alertType === 'expiration') {
    return {
      label: ALERT_TYPE_LABELS.expiration,
      style: { background: 'var(--color-accent-soft)', color: 'var(--color-accent-hover)' },
    }
  }

  if (alertType === 'low_stock') {
    return {
      label: ALERT_TYPE_LABELS.low_stock,
      style: { background: 'var(--color-primary-soft)', color: 'var(--color-danger)' },
    }
  }

  return { label: alertType || '-', style: undefined }
}

export function destructionStatusBadge(status) {
  if (status === 'completed') {
    return {
      label: DESTRUCTION_STATUS_LABELS.completed,
      style: { background: 'var(--color-primary-soft)', color: 'var(--color-success)' },
    }
  }

  return {
    label: DESTRUCTION_STATUS_LABELS[status] || status || '-',
    style: { background: 'var(--color-accent-soft)', color: 'var(--color-accent-hover)' },
  }
}

/* Recherche insensible aux accents et à la casse (convention Patients). */
export function normalizeSearch(value) {
  return String(value ?? '')
    .normalize('NFD')
    .replace(/[\u0300-\u036f]/g, '')
    .toLocaleLowerCase()
}

export function findById(list, id) {
  if (id === null || id === undefined || id === '') return null
  return list.find((entry) => String(entry.id) === String(id)) || null
}

/*
 * Les API de référence n'exposent pas toujours le libellé complet :
 * en cas d'identifiant inconnu (référence inaccessible pour le rôle
 * connecté), l'identifiant brut est affiché, jamais de donnée inventée.
 */
export function itemLabel(items, id) {
  const item = findById(items, id)
  if (item) return item.name || `Article #${item.id}`
  return id === null || id === undefined || id === '' ? '-' : `Article #${id}`
}

export function familyLabel(families, id) {
  const family = findById(families, id)
  if (!family) {
    return id === null || id === undefined || id === '' ? '-' : `Famille #${id}`
  }
  return family.code ? `${family.code} — ${family.name}` : family.name
}

export function categoryLabel(categories, id) {
  const category = findById(categories, id)
  if (!category) {
    return id === null || id === undefined || id === '' ? '-' : `Catégorie #${id}`
  }
  return category.code ? `${category.code} — ${category.name}` : category.name
}

export function unitLabel(units, id) {
  const unit = findById(units, id)
  if (!unit) {
    return id === null || id === undefined || id === '' ? '-' : `Unité #${id}`
  }
  return unit.symbol ? `${unit.name} (${unit.symbol})` : unit.name
}

export function supplierLabel(suppliers, id) {
  const supplier = findById(suppliers, id)
  if (!supplier) {
    return id === null || id === undefined || id === '' ? '-' : `Fournisseur #${id}`
  }
  return supplier.name || `Fournisseur #${supplier.id}`
}

/*
 * Regroupement par ressource des listes chargées en parallèle : une API
 * refusée (403 pour le rôle connecté) n'empêche pas l'affichage des autres.
 */
export function fulfilledValue(result, fallback = []) {
  return result.status === 'fulfilled' && Array.isArray(result.value)
    ? result.value
    : fallback
}
