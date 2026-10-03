import { Link, useSearchParams } from 'react-router-dom'

import Icon from '../components/common/Icon.jsx'
import PageHero from '../components/common/PageHero.jsx'
import SmartImage from '../components/common/SmartImage.jsx'
import { useSiteConfig } from '../context/SiteConfigContext.jsx'

/**
 * Profil d'un praticien.
 * Le praticien est choisi via `?m=Nom du praticien` (depuis la page Équipe).
 * Aucun endpoint praticien n'étant exposé publiquement, les données viennent
 * de la configuration : un futur appel API pourra remplacer ce sourcing.
 */
function Profile() {
  const { config } = useSiteConfig()
  const [searchParams] = useSearchParams()

  const members = config.team.members || []
  const requested = searchParams.get('m')
  const member = members.find((item) => item.name === requested) || members[0]

  if (!member) {
    return (
      <section className="page-shell">
        <h1>Profil</h1>
        <p className="muted">Aucun praticien configuré pour le moment.</p>
        <Link className="btn btn-outline" to="/team">
          Retour à l’équipe
        </Link>
      </section>
    )
  }

  return (
    <>
      <PageHero
        eyebrow={member.role}
        title={member.name}
        description={config.team.intro}
        actions={[{ label: 'Prendre rendez-vous', to: '/contact', variant: 'btn-accent' }]}
      />

      <section className="page-shell">
        <div className="media-section image-left">
          <div className="media-section-visual">
            <div className="media-frame media-frame-narrow">
              <SmartImage src={member.photo} alt={member.name} variant="avatar" />
            </div>
          </div>

          <div className="media-section-content">
            <p className="eyebrow">{config.branding.cabinetName}</p>
            <p className="muted">{member.description}</p>

            <ul className="list-check">
              <li>
                <Icon name="check" size="1.1rem" />
                <span>Consultations sur rendez-vous</span>
              </li>
              <li>
                <Icon name="check" size="1.1rem" />
                <span>Prise en charge des nouveaux patients</span>
              </li>
              <li>
                <Icon name="check" size="1.1rem" />
                <span>Devis et plan de soins avant traitement</span>
              </li>
            </ul>

            <div className="hero-actions">
              <Link className="btn btn-primary" to="/contact">
                Prendre rendez-vous
              </Link>
              <Link className="btn btn-outline" to="/team">
                Voir toute l’équipe
              </Link>
            </div>
          </div>
        </div>
      </section>
    </>
  )
}

export default Profile
