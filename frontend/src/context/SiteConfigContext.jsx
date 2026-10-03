import { createContext, useCallback, useContext, useEffect, useMemo, useState } from 'react'

import {
  clearSiteConfig,
  defaultSiteConfig,
  loadSiteConfig,
  mergeSiteConfig,
  saveSiteConfig,
} from '../config/siteConfig.js'
import { applyTheme, resetTheme } from '../config/theme.js'

const SiteConfigContext = createContext(null)

/**
 * Fournit la configuration du site à tout le frontend.
 * - `config` : configuration courante (défaut + surcharges locales)
 * - `updateConfig` : modification profonde (section partielle)
 * - `saveConfig` : persistance (localStorage aujourd'hui, API demain)
 * - `resetConfig` : retour aux valeurs par défaut
 *
 * Quand l'API d'administration du site existera, seule la persistance
 * (`saveConfig` / `loadSiteConfig`) devra être remplacée par un appel réseau.
 */
export function SiteConfigProvider({ children }) {
  const [config, setConfig] = useState(() => loadSiteConfig())

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

  const saveConfig = useCallback((nextConfig) => {
    const merged = mergeSiteConfig(defaultSiteConfig, nextConfig)
    saveSiteConfig(merged)
    setConfig(merged)
    return merged
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
