import { Link } from 'react-router-dom'

import { useSiteConfig } from '../context/SiteConfigContext.jsx'

/**
 * Logo du site : image configurée si disponible, sinon monogramme généré.
 * Le contenu (nom, sous-titre, logo) vient de `siteConfig.branding`.
 */
function Logo({ name, subtitle }) {
  const { config } = useSiteConfig()
  const branding = config.branding

  const logoName = name ?? branding.cabinetName
  const logoSubtitle = subtitle ?? branding.tagline
  const monogram = (branding.shortName || branding.cabinetName || 'DC')
    .replace(/[^A-Za-zÀ-ÿ]/g, '')
    .slice(0, 2)
    .toUpperCase()

  return (
    <Link to="/" className="site-logo" aria-label={`Accueil — ${logoName}`}>
      <span className="site-logo-mark" aria-hidden="true">
        {branding.logo ? (
          <img src={branding.logo} alt="" width="100%" height="100%" />
        ) : (
          monogram
        )}
      </span>

      <span className="site-logo-text">
        <span className="site-logo-name">{logoName}</span>
        {logoSubtitle && <span className="site-logo-subtitle">{logoSubtitle}</span>}
      </span>
    </Link>
  )
}

export default Logo
