import { createContext, useCallback, useContext, useEffect, useMemo, useState } from 'react'

import {
  clearSiteConfig,
  defaultSiteConfig,
  loadSiteConfig,
  mergeSiteConfig,
  saveSiteConfig,
} from '../config/siteConfig.js'
import { applyTheme, resetTheme } from '../config/theme.js'
import { apiGet, apiPatch } from '../api/client.js'

const SiteConfigContext = createContext(null)

/**
 * Fournit la configuration du site à tout le frontend.
 * - `config` : configuration courante (serveur, avec cache local initial)
 * - `updateConfig` : modification profonde (section partielle)
 * - `saveConfig` : persistance via l'API, avec cache local après succès
 * - `resetConfig` : retour aux valeurs par défaut
 *
 * Le cache local sert à afficher la dernière configuration connue avant
 * l'hydratation depuis le serveur, pas à remplacer une sauvegarde échouée.
 */
export function SiteConfigProvider({ children }) {
  const [config, setConfig] = useState(() => loadSiteConfig())

  useEffect(() => {
    let isMounted = true

    async function hydrateConfig() {
      try {
        const payload = await apiGet('/site-settings/')
        if (!payload?.config || !isMounted) return

        const merged = mergeSiteConfig(defaultSiteConfig, payload.config)
        setConfig(merged)
        saveSiteConfig(merged)
      } catch {
        // Le cache local reste utilisable si le serveur est temporairement inaccessible.
      }
    }

    hydrateConfig()
    return () => {
      isMounted = false
    }
  }, [])

  // Thème appliqué à :root à chaque changement de configuration.
  useEffect(() => {
    if (config.branding?.theme) {
      applyTheme(config.branding.theme)
    }
  }, [config.branding?.theme])

  // Titre du document piloté par la configuration.
  useEffect(() => {
    document.title = config.branding?.cabinetName || 'Cabinet dentaire'
  }, [config.branding?.cabinetName])

  const updateConfig = useCallback((partial) => {
    setConfig((current) => mergeSiteConfig(current, partial || {}))
  }, [])

  const saveConfig = useCallback(async (nextConfig) => {
    const merged = mergeSiteConfig(defaultSiteConfig, nextConfig)
    const payload = await apiPatch('/site-settings/', { config: merged })

    if (!payload?.config || typeof payload.config !== 'object' || Array.isArray(payload.config)) {
      throw new Error('Réponse invalide du serveur lors de la sauvegarde.')
    }

    const combined = mergeSiteConfig(defaultSiteConfig, payload.config)
    setConfig(combined)
    saveSiteConfig(combined)
    return combined
  }, [])

  const resetConfig = useCallback(() => {
    clearSiteConfig()
    resetTheme()
    setConfig(defaultSiteConfig)
  }, [])

  const value = useMemo(
    () => ({ config, updateConfig, saveConfig, resetConfig }),
    [config, resetConfig, saveConfig, updateConfig],
  )

  return <SiteConfigContext.Provider value={value}>{children}</SiteConfigContext.Provider>
}

export function useSiteConfig() {
  const ctx = useContext(SiteConfigContext)
  if (!ctx) {
    throw new Error('useSiteConfig doit être utilisé à l’intérieur de <SiteConfigProvider>.')
  }
  return ctx
}
