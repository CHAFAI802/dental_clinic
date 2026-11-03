import { useEffect, useId, useRef, useState } from 'react'

function TableShell({ children, className = '', style }) {
  const viewportRef = useRef(null)
  const topScrollbarRef = useRef(null)
  const [hasOverflow, setHasOverflow] = useState(false)
  const [contentWidth, setContentWidth] = useState(0)
  const id = useId()
  const viewportId = `table-viewport-${id.replace(/:/g, '')}`

  useEffect(() => {
    const viewport = viewportRef.current
    const table = viewport?.querySelector('table')
    if (!viewport || !table) return undefined

    const updateDimensions = () => {
      const nextWidth = table.scrollWidth
      setContentWidth(nextWidth)
      setHasOverflow(nextWidth > viewport.clientWidth + 1)
    }

    const resizeObserver = new ResizeObserver(updateDimensions)
    resizeObserver.observe(viewport)
    resizeObserver.observe(table)

    const mutationObserver = new MutationObserver(updateDimensions)
    mutationObserver.observe(table, { childList: true, subtree: true, characterData: true })
    updateDimensions()

    return () => {
      resizeObserver.disconnect()
      mutationObserver.disconnect()
    }
  }, [children])

  const syncScroll = (source, target) => {
    if (target && target.scrollLeft !== source.scrollLeft) {
      target.scrollLeft = source.scrollLeft
    }
  }

  return (
    <div className="table-scroll-container">
      {hasOverflow && (
        <div
          ref={topScrollbarRef}
          className="table-top-scrollbar"
          role="region"
          aria-label="Défilement horizontal du tableau"
          aria-controls={viewportId}
          tabIndex={0}
          onScroll={(event) => syncScroll(event.currentTarget, viewportRef.current)}
        >
          <div style={{ width: `${contentWidth}px`, height: '1px' }} />
        </div>
      )}
      <div
        ref={viewportRef}
        id={viewportId}
        className={`table-shell${hasOverflow ? ' table-shell-scrollable' : ''}${className ? ` ${className}` : ''}`}
        style={style}
        onScroll={(event) => syncScroll(event.currentTarget, topScrollbarRef.current)}
      >
        {children}
      </div>
    </div>
  )
}

export default TableShell
