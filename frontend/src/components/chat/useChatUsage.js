import { useCallback, useEffect, useState } from 'react'
import { getChatUsage } from '../../services/chat'

/**
 * Remaining daily messages for the signed-in user. The counter is informational, so a
 * failed fetch only hides it; the real limit is enforced by the backend on send.
 */
export function useChatUsage() {
  const [usage, setUsage] = useState(null)

  const refreshUsage = useCallback(async () => {
    try {
      setUsage(await getChatUsage())
    } catch {
      // Keep the last known value rather than showing an error for a read-only hint.
    }
  }, [])

  useEffect(() => {
    refreshUsage()
  }, [refreshUsage])

  return { usage, refreshUsage }
}
