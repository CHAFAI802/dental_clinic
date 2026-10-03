import { useSiteConfig } from '../../context/SiteConfigContext.jsx'
import Icon from '../common/Icon.jsx'
import MediaBlock from '../common/MediaBlock.jsx'
import Section from '../common/Section.jsx'

function AboutSection({ layout = 'image-right' }) {
  const { config } = useSiteConfig()
  const about = config.about

  return (
    <Section id="about" surface>
      <MediaBlock layout={layout} image={about.image} imageAlt={about.imageAlt} imageVariant="clinic">
        <p className="eyebrow">{about.eyebrow}</p>
        <h2>{about.title}</h2>

        {about.paragraphs?.map((paragraph) => (
          <p key={paragraph}>{paragraph}</p>
        ))}

        {about.bullets?.length > 0 && (
          <ul className="list-check">
            {about.bullets.map((bullet) => (
              <li key={bullet}>
                <Icon name="check" size="1.1rem" />
                <span>{bullet}</span>
              </li>
            ))}
          </ul>
        )}

        {about.highlights?.length > 0 && (
          <div className="about-highlights">
            {about.highlights.map((highlight) => (
              <div className="highlight" key={highlight.label}>
                <span className="highlight-value">{highlight.value}</span>
                <span className="highlight-label">{highlight.label}</span>
              </div>
            ))}
          </div>
        )}
      </MediaBlock>
    </Section>
  )
}

export default AboutSection
