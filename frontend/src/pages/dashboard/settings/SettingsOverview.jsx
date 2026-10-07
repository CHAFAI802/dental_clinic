import { Link } from 'react-router-dom'

/*
 * Vue d'ensemble du Paramétrage : les quatre sections actuellement
 * regroupées ici, présentées avec les cartes du dashboard existant
 * (.dashboard-card / .dashboard-grid, cf. DashboardHome).
 *
 * Aucune logique métier : chaque carte navigue vers la page qui gère
 * réellement la ressource (pages réutilisées, jamais dupliquées).
 */
const SECTIONS = [
  {
    id: 'prestation-categories',
    label: 'Catégories de prestations',
    description: 'Créer, modifier et activer les catégories du catalogue.',
    source: '/api/prestation-categories/',
    to: '/dashboard/settings/prestation-categories',
  },
  {
    id: 'prestations',
    label: 'Prestations',
    description: 'Gérer les actes proposés et leur rattachement à une catégorie.',
    source: '/api/prestations/',
    to: '/dashboard/settings/prestations',
  },
  {
    id: 'prestation-tarifs',
    label: 'Tarifs des prestations',
    description: 'Suivre l’historique des tarifs : montant, taxe et date d’effet.',
    source: '/api/prestation-tarifs/',
    to: '/dashboard/settings/prestation-tarifs',
  },
  {
    id: 'working-hours',
    label: 'Horaires de travail',
    description: 'Configurer les jours et plages horaires de chaque praticien.',
    source: '/api/working-hours/',
    to: '/dashboard/working-hours',
  },
]

function SettingsOverview() {
  return (
    <section>
      <div className="dashboard-page-header">
        <div>
          <h2>Paramétrage</h2>
          <p>Catalogue des prestations et horaires de travail du cabinet.</p>
        </div>
      </div>

      <div className="dashboard-grid">
        {SECTIONS.map((section) => (
          <Link
            key={section.id}
            to={section.to}
            className="dashboard-card dashboard-module-card"
          >
            <h3>{section.label}</h3>

            <p className="dashboard-card-desc">{section.description}</p>

            <p className="dashboard-card-meta">
              <code>{section.source}</code>
            </p>
          </Link>
        ))}
      </div>
    </section>
  )
}

export default SettingsOverview
