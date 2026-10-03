import { useParams } from 'react-router-dom'

import BillingNav from './BillingNav.jsx'
import InvoicesPage from './InvoicesPage.jsx'
import PaymentsPage from './PaymentsPage.jsx'
import PrestationCategoriesPage from './PrestationCategoriesPage.jsx'
import PrestationTarifsPage from './PrestationTarifsPage.jsx'
import PrestationsPage from './PrestationsPage.jsx'

/*
 * Conteneur du module Billing.
 *
 * Sections mappées sur les endpoints réellement déclarés dans
 * billing/urls.py. Aucune autre section n'est proposée.
 */
const SECTION_PAGES = {
  invoices: InvoicesPage,
  payments: PaymentsPage,
  'prestation-categories': PrestationCategoriesPage,
  prestations: PrestationsPage,
  'prestation-tarifs': PrestationTarifsPage,
}

function BillingPage({ section: sectionProp }) {
  const params = useParams()
  const section = sectionProp || params.section || 'invoices'

  const Page = SECTION_PAGES[section]

  return (
    <div>
      <BillingNav activeSection={section} />

      {Page ? (
        <Page />
      ) : (
        <section>
          <div className="dashboard-page-header">
            <div>
              <h2>Facturation</h2>
              <p>Section inconnue : {section}</p>
            </div>
          </div>
          <p className="muted">
            Cette section ne correspond à aucune ressource Billing exposée
            par le backend.
          </p>
        </section>
      )}
    </div>
  )
}

export default BillingPage
