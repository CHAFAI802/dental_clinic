import Hero from '../components/sections/Hero.jsx'
import { SECTION_REGISTRY } from '../components/sections/sectionRegistry.js'
import { useSiteConfig } from '../context/SiteConfigContext.jsx'

/**
 * Page d'accueil : assemblage des sections indépendantes.
 * L'ordre, la visibilité et la disposition des sections sont pilotés par
 * `siteConfig.home.sections` (modifiable depuis /settings/site).
 */
function Home() {
  const { config } = useSiteConfig()
  const sections = config.home?.sections || []

  return (
    <>
      <Hero />

      {sections.map((section) => {
        if (section.enabled === false) return null

        const SectionComponent = SECTION_REGISTRY[section.key]
        if (!SectionComponent) return null

        return <SectionComponent key={section.key} layout={section.layout} />
      })}
    </>
  )
}

export default Home
