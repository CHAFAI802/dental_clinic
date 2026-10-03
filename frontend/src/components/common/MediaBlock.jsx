import SmartImage from './SmartImage.jsx'

/**
 * Bloc « image + texte » réutilisable.
 * `layout` : 'image-left' | 'image-right' (configurable depuis la
 * configuration du site afin de pouvoir changer la disposition à la volée).
 */
function MediaBlock({ layout = 'image-left', image, imageAlt, imageVariant, children }) {
  const safeLayout = layout === 'image-right' ? 'image-right' : 'image-left'

  return (
    <div className={`media-section ${safeLayout}`}>
      <div className="media-section-visual">
        <div className="media-frame">
          <SmartImage src={image} alt={imageAlt} variant={imageVariant} />
        </div>
        <span className="media-accent top-right" aria-hidden="true" />
        <span className="media-accent bottom-left" aria-hidden="true" />
      </div>

      <div className="media-section-content">{children}</div>
    </div>
  )
}

export default MediaBlock
