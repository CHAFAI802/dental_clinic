/*
 * Jeu d'icônes du site public (SVG inline, stroke = currentColor).
 * Ajouter une icône = ajouter une entrée dans PATHS.
 */

const PATHS = {
  tooth: (
    <>
      <path d="M12 3c-1.7 0-2.4.7-3.6.7C6.6 3.7 5 5.2 5 8c0 4 .9 6.2 1.7 8.6.6 1.8.8 4.4 2.4 4.4 1.4 0 1.5-2 2.2-3.6.4-1 .9-1.4 1.7-1.4s1.3.4 1.7 1.4c.7 1.6.8 3.6 2.2 3.6 1.6 0 1.8-2.6 2.4-4.4C18.1 14.2 19 12 19 8c0-2.8-1.6-4.3-3.4-4.3-1.2 0-1.9.7-3.6.7z" />
    </>
  ),
  shield: (
    <>
      <path d="M12 3l7 3v5c0 4.5-3 8.3-7 10-4-1.7-7-5.5-7-10V6l7-3z" />
      <path d="M9 12l2 2 4-4" />
    </>
  ),
  sparkles: (
    <>
      <path d="M12 3l1.6 4.4L18 9l-4.4 1.6L12 15l-1.6-4.4L6 9l4.4-1.6L12 3z" />
      <path d="M18.5 15l.8 2.2 2.2.8-2.2.8-.8 2.2-.8-2.2-2.2-.8 2.2-.8.8-2.2z" />
    </>
  ),
  activity: <path d="M3 12h4l2.5-7 5 14L17 12h4" />,
  layers: (
    <>
      <path d="M12 3l9 5-9 5-9-5 9-5z" />
      <path d="M3 13l9 5 9-5" />
    </>
  ),
  clock: (
    <>
      <circle cx="12" cy="12" r="9" />
      <path d="M12 7v5l3 2" />
    </>
  ),
  mapPin: (
    <>
      <path d="M12 21s7-5.5 7-11a7 7 0 1 0-14 0c0 5.5 7 11 7 11z" />
      <circle cx="12" cy="10" r="2.5" />
    </>
  ),
  creditCard: (
    <>
      <rect x="2.5" y="5.5" width="19" height="13" rx="2" />
      <path d="M2.5 10h19M6 15h4" />
    </>
  ),
  accessibility: (
    <>
      <circle cx="12" cy="5" r="2" />
      <path d="M5 9l7 1.5L19 9M12 10.5V15l4 5M12 15l-4 5" />
    </>
  ),
  bell: (
    <>
      <path d="M18 15V10a6 6 0 1 0-12 0v5l-2 3h16l-2-3z" />
      <path d="M10 21h4" />
    </>
  ),
  check: <path d="M4.5 12.5l5 5 10-11" />,
  phone: (
    <path d="M6.5 3h3l1.5 4-2 1.5a12 12 0 0 0 6 6L16.5 12l4 1.5v3a2 2 0 0 1-2.2 2A16.5 16.5 0 0 1 3.5 5.2 2 2 0 0 1 5.5 3h1z" />
  ),
  mail: (
    <>
      <rect x="3" y="5" width="18" height="14" rx="2" />
      <path d="M3.5 7l8.5 6 8.5-6" />
    </>
  ),
  menu: <path d="M4 7h16M4 12h16M4 17h16" />,
  close: <path d="M6 6l12 12M18 6L6 18" />,
  arrowRight: <path d="M4 12h15m-6-6l6 6-6 6" />,
  star: <path d="M12 4l2.4 5 5.6.7-4 3.9 1 5.4-5-2.7-5 2.7 1-5.4-4-3.9 5.6-.7L12 4z" />,
  users: (
    <>
      <circle cx="9" cy="8" r="3.5" />
      <path d="M2.5 20a6.5 6.5 0 0 1 13 0M16 5.2a3.5 3.5 0 0 1 0 6.6M18 20a6 6 0 0 0-3-5.2" />
    </>
  ),
  monitor: (
    <>
      <rect x="3" y="4" width="18" height="12" rx="2" />
      <path d="M8 20h8M12 16v4" />
    </>
  ),
  calendar: (
    <>
      <rect x="3.5" y="5" width="17" height="16" rx="2" />
      <path d="M3.5 10h17M8 3v4M16 3v4" />
    </>
  ),
}

function Icon({ name, className = '', size, ...rest }) {
  const path = PATHS[name]
  if (!path) return null

  const style = size ? { width: size, height: size } : undefined

  return (
    <svg
      viewBox="0 0 24 24"
      aria-hidden="true"
      focusable="false"
      className={`icon ${className}`.trim()}
      style={style}
      {...rest}
    >
      {path}
    </svg>
  )
}

export default Icon
