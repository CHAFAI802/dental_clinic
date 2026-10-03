import Icon from '../components/common/Icon.jsx'
import PageHero from '../components/common/PageHero.jsx'
import ContactSection from '../components/sections/ContactSection.jsx'
import { useSiteConfig } from '../context/SiteConfigContext.jsx'

/**
 * Page Contact : coordonnées + formulaire (section réutilisée),
 * horaires d’ouverture et consignes d’urgence.
 */
function Contact() {
  const { config } = useSiteConfig()
  const contact = config.contact
  const { phone } = config.branding

  return (
    <>
      <PageHero
        eyebrow={contact.eyebrow}
        title={contact.title}
        description={contact.intro}
        actions={[
          {
            label: `Appeler ${phone}`,
            href: `tel:${phone?.replace(/\s/g, '')}`,
            variant: 'btn-accent',
          },
        ]}
      />

      <ContactSection showHeader={false} />

      <section className="section section-surface">
        <div className="container contact-grid">
          <div>
            <p className="eyebrow">Horaires d’ouverture</p>
            <h2>Quand venir ?</h2>
            <p className="section-intro">{contact.emergency}</p>

            <div className="mt-6">
              <table className="hours-table">
                <thead>
                  <tr>
                    <th scope="col">Jour</th>
                    <th scope="col">Horaires</th>
                  </tr>
                </thead>
                <tbody>
                  {contact.hours?.map((row) => (
                    <tr key={row.label}>
                      <th scope="row">{row.label}</th>
                      <td>{row.value}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>

          <div className="contact-cards">
            <article className="card contact-card">
              <span className="icon-box">
                <Icon name="mapPin" />
              </span>
              <div>
                <strong>Nous trouver</strong>
                <span>{contact.address || config.branding.address}</span>
              </div>
            </article>

            <article className="card contact-card">
              <span className="icon-box">
                <Icon name="calendar" />
              </span>
              <div>
                <strong>Sur rendez-vous</strong>
                <span>Consultations du lundi au samedi, créneaux réservés aux urgences.</span>
              </div>
            </article>

            <article className="card contact-card">
              <span className="icon-box">
                <Icon name="bell" />
              </span>
              <div>
                <strong>Urgences</strong>
                <span>{contact.emergency}</span>
              </div>
            </article>
          </div>
        </div>
      </section>
    </>
  )
}

export default Contact
