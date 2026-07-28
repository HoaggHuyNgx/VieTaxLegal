const placeholderPattern = /\{\{(\w+)\}\}/g

// The replacer-function form of String.replace is load-bearing: a value holding
// `$&` or `$1` — conversation titles are user-supplied — would otherwise be read
// as a capture-group reference and inject the wrong text.
export function interpolate(template, params) {
  if (!params) return template
  return template.replace(placeholderPattern, (match, name) =>
    Object.prototype.hasOwnProperty.call(params, name) ? String(params[name]) : match
  )
}

export function resolveKey(catalog, key) {
  return key.split('.').reduce((node, part) => (node == null ? undefined : node[part]), catalog)
}

// Returns undefined on a miss so the caller can fall back to another catalog.
// t() never returns JSX — a string needing embedded markup is split into
// several keys and joined in the component instead.
export function translate(catalog, key, params) {
  const value = resolveKey(catalog, key)
  if (typeof value !== 'string') return undefined
  return interpolate(value, params)
}

export function readList(catalog, key) {
  const value = resolveKey(catalog, key)
  return Array.isArray(value) ? value : undefined
}
