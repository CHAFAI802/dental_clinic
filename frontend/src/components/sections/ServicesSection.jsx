import { Link } from 'react-router-dom'

import { useSiteConfig } from '../../context/SiteConfigContext.jsx'
import Icon from '../common/Icon.jsx'
import Section from '../common/Section.jsx'

function ServicesSection({ showCta = true, showHeader = true }) {
  const { config } = useSiteConfig()
  const services = config.services

  return (
    <Section
      id="services"
      tinted
      center
      showHeader={showHeader}
      eyebrow={services.eyebrow}
      title={services.title}
      intro={services.intro}
    >
      <div className="cards-grid">
        {services.items?.map((service) => (
          <article className="card service-card" key={service.title}>
            <span className="icon-box">
              <Icon name={service.icon} className="icon-lg" />
            </span>
            <h3 className="card-title">{service.title}</h3>
            <p className="card-text">{service.description}</p>
          </article>
        ))}
      </div>

      {showCta && services.cta?.label && (
        <div className="section-action">
          <Link className="btn btn-outline" to={services.cta.to || '/services'}>
            {services.cta.label}
          </Link>
        </div>
      )}
    </Section>
  )
}

export default ServicesSection
