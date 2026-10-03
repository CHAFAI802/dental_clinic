import { Link } from 'react-router-dom'

import { useSiteConfig } from '../../context/SiteConfigContext.jsx'
import Icon from '../common/Icon.jsx'
import SmartImage from '../common/SmartImage.jsx'

/**
 * Hero de la page d'accueil : tout le contenu vient de `siteConfig.hero`.
 */
function Hero() {
  const { config } = useSiteConfig()
  const { hero, branding } = config

  return (
    <section className="hero">
      <div className="container hero-grid">
        <div className="hero-content">
          {hero.eyebrow && <p className="hero-eyebrow">{hero.eyebrow}</p>}
          {hero.subtitle && <p className="hero-subtitle">{hero.subtitle}</p>}
          <h1>{hero.title}</h1>

          {hero.description && <p className="hero-description">{hero.description}</p>}

          <div className="hero-actions">
            {hero.primaryButton?.label && (
              <Link className="btn btn-accent" to={hero.primaryButton.to || '/contact'}>
                {hero.primaryButton.label}
              </Link>
            )}
            {hero.secondaryButton?.label && (
              <Link className="btn btn-outline-light" to={hero.secondaryButton.to || '/services'}>
                {hero.secondaryButton.label}
              </Link>
            )}
          </div>

          {hero.points?.length > 0 && (
            <ul className="hero-points">
              {hero.points.map((point) => (
                <li key={point}>
                  <Icon name="check" size="1rem" />
                  {point}
                </li>
              ))}
            </ul>
          )}
        </div>

        <div className="hero-visual">
          <div className="media-frame">
            <SmartImage src={hero.image} alt={hero.imageAlt} variant="hero" label={branding.cabinetName} />
          </div>

          {hero.badge?.title && (
            <div className="hero-badge">
              <Icon name="clock" className="icon-lg" />
              <div>
                <strong>{hero.badge.title}</strong>
                <span>{hero.badge.text}</span>
              </div>
            </div>
          )}
        </div>
      </div>
    </section>
  )
}

export default Hero
