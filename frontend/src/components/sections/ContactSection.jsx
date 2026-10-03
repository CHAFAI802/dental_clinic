import { useSiteConfig } from '../../context/SiteConfigContext.jsx'
import ContactForm from '../common/ContactForm.jsx'
import Icon from '../common/Icon.jsx'
import Section from '../common/Section.jsx'

function ContactSection({ showHeader = true }) {
  const { config } = useSiteConfig()
  const contact = config.contact
  const { phone, email, address } = config.branding

  return (
    <Section
      id="contact"
      tinted
      showHeader={showHeader}
      eyebrow={contact.eyebrow}
      title={contact.title}
      intro={contact.intro}
    >
      <div className="contact-grid">
        <div className="contact-cards">
          <article className="card contact-card">
            <span className="icon-box">
              <Icon name="phone" />
            </span>
            <div>
              <strong>Téléphone</strong>
              <a href={`tel:${phone?.replace(/\s/g, '')}`}>{phone}</a>
            </div>
          </article>

          <article className="card contact-card">
            <span className="icon-box">
              <Icon name="mail" />
            </span>
            <div>
              <strong>Email</strong>
              <a href={`mailto:${email}`}>{email}</a>
            </div>
          </article>

          <article className="card contact-card">
            <span className="icon-box">
              <Icon name="mapPin" />
            </span>
            <div>
              <strong>Adresse</strong>
              <span>{address}</span>
            </div>
          </article>
        </div>

        <div className="card">
          <ContactForm />
        </div>
      </div>
    </Section>
  )
}

export default ContactSection
