import { Link } from 'react-router-dom'

/**
 * Bannière de page utilisée par les pages internes (Services, Équipe,
 * Contact, Paramétrage…) pour garantir la même identité qu'à l'accueil.
 */
function PageHero({ eyebrow, title, description, actions = [] }) {
  return (
    <section className="page-hero">
      <div className="container">
        {eyebrow && <p className="eyebrow">{eyebrow}</p>}
        <h1>{title}</h1>
        {description && <p>{description}</p>}

        {actions.length > 0 && (
          <div className="page-hero-actions">
            {actions.map((action, index) => {
              const key = `${action.label}-${index}`
              const className = `btn ${action.variant || 'btn-accent'}`

              if (action.href) {
                return (
                  <a key={key} className={className} href={action.href}>
                    {action.label}
                  </a>
                )
              }

              return (
                <Link key={key} className={className} to={action.to || '/'}>
                  {action.label}
                </Link>
              )
            })}
          </div>
        )}
      </div>
    </section>
  )
}

export default PageHero
