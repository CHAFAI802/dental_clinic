import { useSiteConfig } from '../../context/SiteConfigContext.jsx'
import Section from '../common/Section.jsx'

function TestimonialsSection() {
  const { config } = useSiteConfig()
  const testimonials = config.testimonials

  return (
    <Section
      id="testimonials"
      tinted
      center
      eyebrow={testimonials.eyebrow}
      title={testimonials.title}
    >
      <div className="cards-grid">
        {testimonials.items?.map((item) => (
          <article className="card testimonial-card" key={item.author}>
            <span className="testimonial-stars" aria-label={`${item.stars} étoiles`}>
              {'★'.repeat(item.stars || 5)}
            </span>
            <blockquote className="testimonial-quote">{item.quote}</blockquote>
            <footer className="testimonial-author">
              <strong>{item.author}</strong>
              <span>{item.role}</span>
            </footer>
          </article>
        ))}
      </div>
    </Section>
  )
}

export default TestimonialsSection
