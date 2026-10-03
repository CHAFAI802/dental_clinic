import { Link } from 'react-router-dom'

import { useAuth } from '../../../context/AuthContext.jsx'

/*
 * Sections Billing réellement exposées par le backend (billing/urls.py).
 *
 * Visibilité déduite des permissions backend :
 * - InvoicePermission            → GET : accountant, receptionist, administrator, super_admin
 * - PaymentViewSet               → IsAccountantOrAdmin : super_admin, administrator, accountant
 * - PrestationCategoryViewSet    → IsAdministrator : super_admin, administrator
 * - PrestationViewSet            → IsAdministrator : super_admin, administrator
 * - PrestationTarifViewSet       → IsAdministrator : super_admin, administrator
 *
 * Le backend reste l'autorité de sécurité : ces règles servent uniquement
 * à masquer les onglets inaccessibles (meilleure UX).
 */
const SECTIONS = [
  {
    id: 'invoices',
    label: 'Factures',
    roles: ['super_admin', 'administrator', 'accountant', 'receptionist'],
  },
  {
    id: 'payments',
    label: 'Paiements',
    roles: ['super_admin', 'administrator', 'accountant'],
  },
  {
    id: 'prestation-categories',
    label: 'Catégories de prestations',
    roles: ['super_admin', 'administrator'],
  },
  {
    id: 'prestations',
    label: 'Prestations',
    roles: ['super_admin', 'administrator'],
  },
  {
    id: 'prestation-tarifs',
    label: 'Tarifs des prestations',
    roles: ['super_admin', 'administrator'],
  },
]

function BillingNav({ activeSection }) {
  const { user: currentUser } = useAuth()

  const visible = SECTIONS.filter((section) =>
    section.roles.includes(currentUser?.role),
  )

  if (visible.length < 2) return null

  return (
    <nav
      className="dashboard-nav"
      aria-label="Navigation facturation"
      style={{
        display: 'flex',
        flexWrap: 'wrap',
        gap: 'var(--space-2)',
        marginBottom: 'var(--space-4)',
      }}
    >
      {visible.map((section) => (
        <Link
          key={section.id}
          to={`/dashboard/billing/${section.id}`}
          className={activeSection === section.id ? 'active' : undefined}
        >
          {section.label}
        </Link>
      ))}
    </nav>
  )
}

export default BillingNav
