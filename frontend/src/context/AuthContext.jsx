import { useCallback, useEffect, useMemo, useState } from 'react'
import { setSessionExpiredHandler } from '../services/api'
import {
  getCurrentUser,
  login as loginRequest,
  logout as logoutRequest,
  register as registerRequest,
} from '../services/auth'
import AuthContext from './auth-context'

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null)
  const [isLoading, setIsLoading] = useState(true)

  const refreshSession = useCallback(async () => {
    try {
      const currentUser = await getCurrentUser()
      setUser(currentUser)
      return currentUser
    } catch {
      setUser(null)
      return null
    } finally {
      setIsLoading(false)
    }
  }, [])

  useEffect(() => {
    refreshSession()
  }, [refreshSession])

  // A session that can no longer be renewed signs the user out here too; ProtectedRoute then
  // leaves the page instead of every request on it failing.
  useEffect(() => {
    setSessionExpiredHandler(() => setUser(null))
    return () => setSessionExpiredHandler(null)
  }, [])

  const register = useCallback(async (payload) => {
    const registeredUser = await registerRequest(payload)
    setUser(registeredUser)
    return registeredUser
  }, [])

  const login = useCallback(async (payload) => {
    const loggedInUser = await loginRequest(payload)
    setUser(loggedInUser)
    return loggedInUser
  }, [])

  const logout = useCallback(async () => {
    await logoutRequest()
    setUser(null)
  }, [])

  const value = useMemo(
    () => ({ user, isLoading, register, login, logout, refreshSession }),
    [isLoading, login, logout, refreshSession, register, user]
  )

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}
