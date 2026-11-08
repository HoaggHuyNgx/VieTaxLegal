import { useCallback, useEffect, useState } from 'react'
import { ADMIN_PAGE_SIZE, listUsers, updateUser } from '../../services/admin'

// Errors are kept as the raw ApiError and translated at render, so a language switch
// re-renders them without refetching.
export function useAdminUsers() {
  const [users, setUsers] = useState([])
  const [offset, setOffset] = useState(0)
  const [hasMore, setHasMore] = useState(false)
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState(null)
  const [savingId, setSavingId] = useState(null)

  useEffect(() => {
    let cancelled = false
    listUsers({ offset })
      .then((page) => {
        if (cancelled) return
        setUsers(page)
        setHasMore(page.length === ADMIN_PAGE_SIZE)
        setError(null)
      })
      .catch((loadError) => {
        if (!cancelled) setError(loadError)
      })
      .finally(() => {
        if (!cancelled) setIsLoading(false)
      })
    return () => {
      cancelled = true
    }
  }, [offset])

  const changeUser = useCallback(async (userId, changes) => {
    setSavingId(userId)
    try {
      const updated = await updateUser(userId, changes)
      setUsers((current) => current.map((user) => (user.id === userId ? updated : user)))
      setError(null)
    } catch (saveError) {
      setError(saveError)
    } finally {
      setSavingId(null)
    }
  }, [])

  const goToPage = useCallback((nextOffset) => {
    setIsLoading(true)
    setOffset(Math.max(0, nextOffset))
  }, [])

  return { users, offset, hasMore, isLoading, error, savingId, changeUser, goToPage }
}
