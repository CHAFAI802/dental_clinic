import { Link } from 'react-router-dom'

import { useSiteConfig } from '../../context/SiteConfigContext.jsx'
import SmartImage from '../common/SmartImage.jsx'
import Section from '../common/Section.jsx'

function TeamSection({ showCta = true, showHeader = true }) {
  const { config } = useSiteConfig()
  const team = config.team

  return (
    <Section
      id="team"
      surface
      center
      showHeader={showHeader}
      eyebrow={team.eyebrow}
      title={team.title}
      intro={team.intro}
    >
      <div className="team-grid">
        {team.members?.map((member) => (
          <article className="card team-card" key={member.name}>
            <div className="team-avatar">
              <SmartImage src={member.photo} alt={member.name} variant="avatar" />
            </div>
            <span className="team-role">{member.role}</span>
            <h3 className="card-title">
              <Link className="team-link" to={`/team/profile?m=${encodeURIComponent(member.name)}`}>
                {member.name}
              </Link>
            </h3>
            <p className="card-text">{member.description}</p>
          </article>
        ))}
      </div>

      {showCta && team.cta?.label && (
        <div className="section-action">
          <Link className="btn btn-outline" to={team.cta.to || '/team'}>
            {team.cta.label}
          </Link>
        </div>
      )}
    </Section>
  )
}

export default TeamSection
