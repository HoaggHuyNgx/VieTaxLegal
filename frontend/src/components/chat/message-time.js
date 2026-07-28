// Returns null when a timestamp cannot be displayed so the caller can render
// its localized "just now" fallback.
export function formatMessageTime(value, localeTag) {
  if (!value) return null
  const date = new Date(value)
  if (Number.isNaN(date.getTime())) return null
  return date.toLocaleTimeString(localeTag, { hour: '2-digit', minute: '2-digit' })
}
