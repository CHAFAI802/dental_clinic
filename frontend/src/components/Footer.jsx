import { Link } from 'react-router-dom'

import { useSiteConfig } from '../context/SiteConfigContext.jsx'
import Icon from './common/Icon.jsx'
import Logo from './logo.jsx'

/**
 * Pied de page : identité, navigation, coordonnées, horaires, réseaux sociaux.
 * Tout le contenu provient de `siteConfig` (footer + branding).
 */
function Footer() {
  const { config } = useSiteConfig()
  const { footer, branding } = config

  const contactItems = [
    { icon: 'mapPin', value: branding.address },
    { icon: 'phone', value: branding.phone, href: `tel:${branding.phone?.replace(/\s/g, '')}` },
    { icon: 'mail', value: branding.email, href: `mailto:${branding.email}` },
  ]

  return (
    <footer className="footer-bar">
      <div className="container">
        <div className="footer-grid">
          <div className="footer-brand">
            <Logo />
            {footer.description && <p className="footer-description">{footer.description}</p>}

            {footer.showSocials && branding.socials?.length > 0 && (
              <div className="footer-socials">
                {branding.socials.map((social) => (
                  <a
                    key={social.label}
                    href={social.url}
                    target="_blank"
                    rel="noreferrer noopener"
                    aria-label={social.label}
                    title={social.label}
                  >
                    {social.label.slice(0, 2).toUpperCase()}
                  </a>
                ))}
              </div>
            )}
          </div>

          {footer.columns?.map((column) => (
            <div className="footer-column" key={column.title}>
              <h3>{column.title}</h3>

              {column.links && (
                <ul>
                  {column.links.map((link) => (
                    <li key={link.to}>
                      <Link to={link.to}>{link.label}</Link>
                    </li>
                  ))}
                </ul>
              )}

              {column.items && (
                <ul>
                  {column.items.map((item) => (
                    <li key={item.label}>
                      <span>
                        <strong>{item.label}</strong> : {item.value}
                      </span>
                    </li>
                  ))}
                </ul>
              )}
            </div>
          ))}

          <div className="footer-column">
            <h3>Contact</h3>
            <ul>
              {contactItems.map((item) => (
                <li key={item.icon} className="footer-contact-item">
                  <Icon name={item.icon} />
                  {item.href ? (
                    <a href={item.href}>{item.value}</a>
                  ) : (
                    <span>{item.value}</span>
                  )}
                </li>
              ))}
            </ul>
          </div>
        </div>

        <div className="footer-bottom">
          <span>
            © {new Date().getFullYear()} {branding.cabinetName} — {footer.copyright}
          </span>
          {footer.legal && <span>{footer.legal}</span>}
          <span>
            <Link to="/settings/site">Paramétrage du site</Link>
          </span>
        </div>
      </div>
    </footer>
  )
}

export default Footer
