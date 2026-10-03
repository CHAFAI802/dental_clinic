import AboutSection from './AboutSection.jsx'
import ContactSection from './ContactSection.jsx'
import CtaSection from './CtaSection.jsx'
import InfoSection from './InfoSection.jsx'
import ServicesSection from './ServicesSection.jsx'
import StepsSection from './StepsSection.jsx'
import TeamSection from './TeamSection.jsx'
import TechnologySection from './TechnologySection.jsx'
import TestimonialsSection from './TestimonialsSection.jsx'

/**
 * Registre des sections de la page d'accueil.
 * `siteConfig.home.sections` référence ces clés ; ajouter une section =
 * créer le composant + l'enregistrer ici (aucune modification backend).
 */
export const SECTION_REGISTRY = {
  about: AboutSection,
  services: ServicesSection,
  steps: StepsSection,
  team: TeamSection,
  technology: TechnologySection,
  testimonials: TestimonialsSection,
  info: InfoSection,
  cta: CtaSection,
  contact: ContactSection,
}

export default SECTION_REGISTRY
