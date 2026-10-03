import { useSiteConfig } from '../../context/SiteConfigContext.jsx'
import Icon from '../common/Icon.jsx'
import MediaBlock from '../common/MediaBlock.jsx'
import Section from '../common/Section.jsx'

function TechnologySection({ layout = 'image-left' }) {
  const { config } = useSiteConfig()
  const technology = config.technology

  return (
    <Section id="technology" tinted>
      <MediaBlock layout={layout} image={technology.image} imageAlt={technology.imageAlt} imageVariant="tech">
        <p className="eyebrow">{technology.eyebrow}</p>
        <h2>{technology.title}</h2>

        {technology.paragraphs?.map((paragraph) => (
          <p key={paragraph}>{paragraph}</p>
        ))}

        <div className="tech-list">
          {technology.items?.map((item) => (
            <div className="tech-item" key={item.title}>
              <span className="icon-box accent" aria-hidden="true">
                <Icon name="monitor" />
              </span>
              <div>
                <strong>{item.title}</strong>
                <p>{item.description}</p>
              </div>
            </div>
          ))}
        </div>
      </MediaBlock>
    </Section>
  )
}

export default TechnologySection
