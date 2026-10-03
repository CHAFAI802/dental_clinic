import CtaSection from '../components/sections/CtaSection.jsx'
import ServicesSection from '../components/sections/ServicesSection.jsx'
import PageHero from '../components/common/PageHero.jsx'
import { useSiteConfig } from '../context/SiteConfigContext.jsx'

/**
 * Page Services : réutilise la section configurée de l'accueil
 * pour garantir une identité visuelle strictement identique.
 */
function Services() {
  const { config } = useSiteConfig()
  const services = config.services

  return (
    <>
      <PageHero
        eyebrow={services.eyebrow}
        title={services.title}
        description={services.intro}
        actions={[{ label: config.nav.cta.label, to: config.nav.cta.to, variant: 'btn-accent' }]}
      />
      <ServicesSection showCta={false} showHeader={false} />
      <CtaSection />
    </>
  )
}

export default Services
