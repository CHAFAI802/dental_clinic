/*
 * Illustrations vectorielles utilisées quand aucune image n'est configurée
 * (siteConfig : `image: null`). Dès qu'une URL est fournie, les composants
 * affichent un <img> à la place.
 *
 * Elles se colorent avec les variables CSS du thème.
 */

const PALETTES = {
  hero: { bg: 'var(--color-primary-hover)', shape: 'rgba(255,255,255,0.10)', accent: 'var(--color-accent)' },
  clinic: { bg: 'var(--color-primary-soft)', shape: 'rgba(20,33,61,0.08)', accent: 'var(--color-secondary)' },
  tech: { bg: 'var(--color-secondary-soft)', shape: 'rgba(45,106,159,0.12)', accent: 'var(--color-secondary)' },
  team: { bg: 'var(--color-accent-soft)', shape: 'rgba(252,163,17,0.18)', accent: 'var(--color-accent-hover)' },
  avatar: { bg: 'var(--color-primary-soft)', shape: 'rgba(20,33,61,0.10)', accent: 'var(--color-secondary)' },
}

function ToothGlyph({ fill, stroke }) {
  return (
    <path
      d="M200 118c-24 0-34 12-52 12-27 0-49 22-49 66 0 58 14 90 25 125 9 26 12 64 35 64 20 0 22-30 32-53 6-15 13-21 25-21s19 6 25 21c10 23 12 53 32 53 23 0 26-38 35-64 11-35 25-67 25-125 0-44-22-66-49-66-18 0-28-12-52-12z"
      fill={fill}
      stroke={stroke}
      strokeWidth="6"
      strokeLinejoin="round"
    />
  )
}

function Illustration({ variant = 'clinic', label, className = '' }) {
  const palette = PALETTES[variant] || PALETTES.clinic
  const isAvatar = variant === 'avatar'

  if (isAvatar) {
    return (
      <svg viewBox="0 0 200 200" role="img" aria-label={label || ''} className={className}>
        <rect width="200" height="200" fill={palette.bg} />
        <circle cx="100" cy="78" r="34" style={{ fill: palette.accent }} />
        <path
          d="M32 190c0-38 30-64 68-64s68 26 68 64"
          style={{ fill: palette.shape }}
        />
        <path
          d="M32 190c0-38 30-64 68-64s68 26 68 64"
          style={{ fill: palette.accent, opacity: 0.35 }}
        />
      </svg>
    )
  }

  return (
    <svg
      viewBox="0 0 560 400"
      role="img"
      aria-label={label || ''}
      className={className}
      preserveAspectRatio="xMidYMid slice"
    >
      <rect width="560" height="400" fill={palette.bg} />
      <circle cx="470" cy="70" r="130" style={{ fill: palette.shape }} />
      <circle cx="70" cy="350" r="110" style={{ fill: palette.shape }} />

      {variant === 'tech' ? (
        <g style={{ stroke: palette.accent }} fill="none" strokeWidth="3">
          <rect x="120" y="90" width="320" height="220" rx="18" opacity="0.5" />
          <path d="M120 200h320M280 90v220" opacity="0.35" />
          <path d="M150 250c40-60 80 40 120-30s80 20 140-40" strokeWidth="4" />
          <circle cx="280" cy="200" r="8" fill={palette.accent} />
        </g>
      ) : variant === 'team' ? (
        <g>
          <circle cx="200" cy="170" r="52" style={{ fill: palette.accent }} />
          <circle cx="360" cy="170" r="52" style={{ fill: palette.shape }} />
          <path d="M120 330c0-44 36-76 80-76s80 32 80 76" style={{ fill: palette.shape }} />
          <path d="M280 330c0-44 36-76 80-76s80 32 80 76" style={{ fill: palette.accent, opacity: 0.5 }} />
        </g>
      ) : (
        <g transform="translate(160 70) scale(1.05)">
          <ToothGlyph fill="rgba(255,255,255,0.92)" stroke={palette.accent} />
          <circle cx="245" cy="60" r="16" style={{ fill: palette.accent }} />
          <path
            d="M300 150l10 26 26 10-26 10-10 26-10-26-26-10 26-10 10-26z"
            style={{ fill: palette.accent }}
            opacity="0.85"
          />
        </g>
      )}
    </svg>
  )
}

export default Illustration
