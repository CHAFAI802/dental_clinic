import { useSiteConfig } from '../../context/SiteConfigContext.jsx'
import Icon from '../common/Icon.jsx'
import Section from '../common/Section.jsx'

/**
 * Informations pratiques : accès, horaires, paiement…
 * Les horaires viennent de `contact.hours` (source unique réutilisée
 * par le footer et la page Contact).
 */
function InfoSection() {
  const { config } = useSiteConfig()
  const info = config.info
  const hours = config.contact.hours

  return (
    <Section
      id="info"
      surface
      eyebrow={info.eyebrow}
      title={info.title}
      intro={info.paragraphs?.[0]}
    >
      <div className="info-grid">
        <div className="cards-grid">
          {info.items?.map((item) => (
            <article className="card" key={item.title}>
              <span className="icon-box">
                <Icon name={item.icon} />
              </span>
              <h3 className="card-title">{item.title}</h3>
              <p className="card-text">{item.text}</p>
            </article>
          ))}
        </div>

        <div>
          <table className="hours-table">
            <thead>
              <tr>
                <th scope="col">Jour</th>
                <th scope="col">Horaires</th>
              </tr>
            </thead>
            <tbody>
              {hours?.map((row) => (
                <tr key={row.label}>
                  <th scope="row">{row.label}</th>
                  <td>{row.value}</td>
                </tr>
              ))}
            </tbody>
          </table>

          {config.contact.emergency && (
            <p className="contact-note">{config.contact.emergency}</p>
          )}
        </div>
      </div>
    </Section>
  )
}

export default InfoSection
