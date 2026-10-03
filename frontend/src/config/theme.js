/*
 * Miroir JavaScript des jetons de thème (variables.css).
 * Utilisé par le paramétrage du site (/settings/site) pour appliquer
 * en temps réel de nouvelles couleurs sans recompiler le CSS.
 *
 * La clé correspond au nom de variable CSS sans le préfixe "--".
 */

export const DEFAULT_THEME = {
  primary: '#14213d',
  primaryHover: '#1e3054',
  secondary: '#2d6a9f',
  accent: '#fca311',
  background: '#f4f7fb',
  surface: '#ffffff',
  text: '#0f172a',
  textMuted: '#475569',
  border: '#e5e7eb',
}

const CSS_VARIABLE_BY_THEME_KEY = {
  primary: '--color-primary',
  primaryHover: '--color-primary-hover',
  secondary: '--color-secondary',
  accent: '--color-accent',
  background: '--color-background',
  surface: '--color-surface',
  text: '--color-text',
  textMuted: '--color-text-muted',
  border: '--color-border',
}

/**
 * Applique un thème (partiel) sur :root.
 * Les clés absentes du thème laissent la valeur CSS par défaut inchangée.
 */
export function applyTheme(theme = {}) {
  const root = document.documentElement

  Object.entries(CSS_VARIABLE_BY_THEME_KEY).forEach(([key, cssVar]) => {
    const value = theme[key]
    if (typeof value === 'string' && value.trim()) {
      root.style.setProperty(cssVar, value.trim())
    }
  })
}

export function resetTheme() {
  const root = document.documentElement
  Object.values(CSS_VARIABLE_BY_THEME_KEY).forEach((cssVar) => {
    root.style.removeProperty(cssVar)
  })
}
