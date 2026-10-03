import Illustration from './Illustration.jsx'

/**
 * Affiche l'image configurée si elle existe, sinon une illustration
 * vectorielle aux couleurs du thème. Évite tout lien mort tant que
 * l'administration du site ne fournit pas d'images.
 */
function SmartImage({ src, alt = '', variant = 'clinic', className = '', label }) {
  if (src) {
    return <img src={src} alt={alt} className={className} loading="lazy" />
  }

  return <Illustration variant={variant} label={label || alt} className={className} />
}

export default SmartImage
