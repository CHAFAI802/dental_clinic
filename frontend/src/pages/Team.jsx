import PageHero from '../components/common/PageHero.jsx'
import TeamSection from '../components/sections/TeamSection.jsx'
import { useSiteConfig } from '../context/SiteConfigContext.jsx'

/**
 * Page Équipe : réutilise la section configurée de l'accueil.
 */
function Team() {
  const { config } = useSiteConfig()
  const team = config.team

  return (
    <>
      <PageHero
        eyebrow={team.eyebrow}
        title={team.title}
        description={team.intro}
        actions={[{ label: config.nav.cta.label, to: config.nav.cta.to, variant: 'btn-accent' }]}
      />
      <TeamSection showCta={false} showHeader={false} />
    </>
  )
}

export default Team
