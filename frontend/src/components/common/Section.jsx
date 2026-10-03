/**
 * Conteneur de section générique : en-tête configurable + contenu.
 * Toutes les sections de la page d'accueil passent par ce composant
 * pour garantir un espacement et une typographie identiques.
 */
function Section({
  id,
  title,
  eyebrow,
  intro,
  center = false,
  surface = false,
  tinted = false,
  showHeader = true,
  className = '',
  headerExtra = null,
  children,
}) {
  const classNames = [
    'section',
    surface ? 'section-surface' : '',
    tinted ? 'section-tinted' : '',
    className,
  ]
    .filter(Boolean)
    .join(' ')

  return (
    <section id={id} className={classNames}>
      <div className="container">
        {showHeader && (eyebrow || title || intro) && (
          <header className={`section-header${center ? ' center' : ''}`}>
            {eyebrow && <p className="eyebrow">{eyebrow}</p>}
            {title && <h2>{title}</h2>}
            {intro && <p className="section-intro">{intro}</p>}
            {headerExtra}
          </header>
        )}

        {children}
      </div>
    </section>
  )
}

export default Section
