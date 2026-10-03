import { Link } from 'react-router-dom'

import { useSiteConfig } from '../../context/SiteConfigContext.jsx'

function CtaSection() {
  const { config } = useSiteConfig()
  const cta = config.cta

  return (
    <section className="section cta-band" id="cta">
      <div className="container cta-band-inner">
        <div>
          <h2>{cta.title}</h2>
          <p>{cta.text}</p>
        </div>

        <div className="cta-band-actions">
          {cta.primaryButton?.label && (
            <Link className="btn btn-accent" to={cta.primaryButton.to || '/contact'}>
              {cta.primaryButton.label}
            </Link>
          )}
          {cta.secondaryButton?.label && cta.secondaryButton.href && (
            <a className="btn btn-outline-light" href={cta.secondaryButton.href}>
              {cta.secondaryButton.label}
            </a>
          )}
        </div>
      </div>
    </section>
  )
}

export default CtaSection
