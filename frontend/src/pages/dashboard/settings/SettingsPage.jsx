import { Link } from 'react-router-dom'
import {
  FolderPlus,
  Stethoscope,
  BadgeEuro,
  CalendarClock,
  Globe,
} from 'lucide-react'

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
    icon: FolderPlus,
    to: '/dashboard/settings/prestation-categories',
  },
  {
    id: 'prestations',
    label: 'Prestations',
    description: 'Gérer les actes proposés et leur rattachement à une catégorie.',
    icon: Stethoscope,
    to: '/dashboard/settings/prestations',
  },
  {
    id: 'prestation-tarifs',
    label: 'Tarifs des prestations',
    description: 'Suivre l’historique des tarifs : montant, taxe et date d’effet.',
    icon: BadgeEuro,
    to: '/dashboard/settings/prestation-tarifs',
  },
  {
    id: 'working-hours',
    label: 'Horaires de travail',
    description: 'Configurer les jours et plages horaires de chaque praticien.',
    icon: CalendarClock,
    to: '/dashboard/working-hours',
  },
  {
    id: 'site',
    label: 'Paramétrage du site',
    description: 'Gérer les paramètres généraux du site.',
    icon: Globe,
    to: '/settings/site',
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
        {SECTIONS.map((section) => {
          const Icon = section.icon

          return (
            <Link
              key={section.id}
              to={section.to}
              className="dashboard-card dashboard-module-card"
            >
              <div className="dashboard-module-icon">
                <Icon size={42} strokeWidth={1.8} />
              </div>

              <h3>{section.label}</h3>

              <p className="dashboard-card-desc">{section.description}</p>
            </Link>
          )
        })}
      </div>
    </section>
  )
}

export default SettingsOverview

