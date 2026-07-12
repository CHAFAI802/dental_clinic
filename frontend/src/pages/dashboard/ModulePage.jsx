import { useMemo } from 'react'
import { useParams } from 'react-router-dom'

import { useAuth } from '../../context/AuthContext.jsx'

function ModulePage() {
  const { moduleId } = useParams()
  const { accessibleModules } = useAuth()

  const module = useMemo(() => {
    if (!Array.isArray(accessibleModules)) return null
    return accessibleModules.find((m) => m.id === moduleId) || null
  }, [accessibleModules, moduleId])

  if (!module) {
    return (
      <section>
        <h2>Module introuvable</h2>
        <p>Ce module n’est pas accessible avec votre compte.</p>
      </section>
    )
  }

  return (
    <section>
      <h2>{module.name}</h2>
      <p>{module.description}</p>

      <h3>État d’intégration</h3>
      <p>
        Le backend expose ce module, mais l’interface React n’est pas encore intégrée pour cette ressource.
      </p>

      <h3>API</h3>
      <p>
        Endpoint : <code>{module.path}</code>
      </p>
      <p>
        <a href={module.path} target="_blank" rel="noreferrer">
          Ouvrir la réponse API
        </a>
      </p>
    </section>
  )
}

export default ModulePage
