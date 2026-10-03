import { useSiteConfig } from '../../context/SiteConfigContext.jsx'
import Section from '../common/Section.jsx'

function StepsSection() {
  const { config } = useSiteConfig()
  const steps = config.steps

  return (
    <Section
      id="steps"
      surface
      center
      eyebrow={steps.eyebrow}
      title={steps.title}
      intro={steps.intro}
    >
      <div className="steps">
        {steps.items?.map((step) => (
          <article className="step" key={step.title}>
            <h3>{step.title}</h3>
            <p>{step.description}</p>
          </article>
        ))}
      </div>
    </Section>
  )
}

export default StepsSection
