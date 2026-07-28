// Translation happens once, at the render boundary. services/ only ever carries
// a `code`, never a language.
//
// CHAT_IN_PROGRESS has call-site variants. UNAUTHENTICATED stays flat even
// though the backend emits two sentences: its shared code gives the frontend no
// way to distinguish them, so both collapse to the existing catalog wording.
//
// t() echoes the key back on a miss, which is how a lookup failure is detected.
function lookup(t, key) {
  const value = t(key)
  return value === key ? undefined : value
}

export function translateApiError(t, error, { variant, fallbackKey } = {}) {
  const code = error?.code

  if (code) {
    const base = `errors.byCode.${code}`
    const translated =
      (variant && lookup(t, `${base}.${variant}`)) ?? lookup(t, `${base}.general`) ?? lookup(t, base)
    // Falls back to the server's Vietnamese copy rather than showing nothing.
    const serverMessage = error.message === code ? undefined : error.message
    const resolved = translated ?? serverMessage
    if (resolved) return resolved
  }

  return t(fallbackKey || 'errors.byCode.REQUEST_FAILED')
}
