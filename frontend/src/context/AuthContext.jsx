import { createContext, useCallback, useContext, useEffect, useMemo, useState } from 'react'

import { apiGet, apiPost } from '../api/client.js'
import { AUTH_TOKEN_STORAGE_KEY } from '../config/api.js'

const AuthContext = createContext(null)

export function AuthProvider({ children }) {
  const [token, setToken] = useState(() => localStorage.getItem(AUTH_TOKEN_STORAGE_KEY))
  const [user, setUser] = useState(null)
  const [roleLabel, setRoleLabel] = useState('')
  const [accessibleModules, setAccessibleModules] = useState([])
  const [isLoading, setIsLoading] = useState(true)

  const clearAuth = useCallback(() => {
    localStorage.removeItem(AUTH_TOKEN_STORAGE_KEY)
    setToken(null)
    setUser(null)
    setRoleLabel('')
    setAccessibleModules([])
  }, [])

  const refreshMe = useCallback(async () => {
    const stored = localStorage.getItem(AUTH_TOKEN_STORAGE_KEY)
    if (!stored) {
      clearAuth()
      setIsLoading(false)
      return
    }

    setToken(stored)
    setIsLoading(true)

    try {
      const data = await apiGet('/auth/me/', { token: stored })
      setUser(data.user)
      setRoleLabel(data.role_label || '')
      setAccessibleModules(Array.isArray(data.accessible_modules) ? data.accessible_modules : [])
    } catch (err) {
      // Token expired/invalid or user no longer allowed.
      if (err?.status === 401 || err?.status === 403) {
        clearAuth()
      }
      throw err
    } finally {
      setIsLoading(false)
    }
  }, [clearAuth])

  useEffect(() => {
    refreshMe().catch(() => {
      // Errors are handled by clearing auth when needed.
    })
  }, [refreshMe])

  const login = useCallback(async ({ email, password }) => {
    const data = await apiPost('/auth/login/', { email, password })

    if (!data?.token) {
      throw new Error("Réponse d'authentification invalide.")
    }

    localStorage.setItem(AUTH_TOKEN_STORAGE_KEY, data.token)
    setToken(data.token)
    setUser(data.user || null)
    setRoleLabel(data.role_label || '')
    setAccessibleModules(Array.isArray(data.accessible_modules) ? data.accessible_modules : [])

    return data
  }, [])

  const logout = useCallback(async () => {
    const stored = localStorage.getItem(AUTH_TOKEN_STORAGE_KEY)
    try {
      if (stored) {
        await apiPost('/auth/logout/', null, { token: stored })
      }
    } catch {
      // Best-effort: even if the token is already invalid, we still clear local state.
    } finally {
      clearAuth()
    }
  }, [clearAuth])

  const value = useMemo(
    () => ({
      user,
      roleLabel,
      accessibleModules,
      token,
      isLoading,
      isAuthenticated: Boolean(token && user),
      login,
      logout,
      refreshMe,
    }),
    [accessibleModules, isLoading, login, logout, refreshMe, roleLabel, token, user],
  )

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}

export function useAuth() {
  const ctx = useContext(AuthContext)
  if (!ctx) {
    throw new Error('useAuth doit être utilisé à l’intérieur de <AuthProvider>.')
  }
  return ctx
}
