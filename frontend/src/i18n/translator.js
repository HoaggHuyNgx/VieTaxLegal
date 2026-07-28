import { DEFAULT_LOCALE, catalogFor } from './catalogs'
import { readList, translate } from './translate'

export function createTranslator(locale) {
  const activeCatalog = catalogFor(locale)
  const fallbackCatalog = catalogFor(DEFAULT_LOCALE)

  // Falls back to the default catalog so a key missing only from `en` still
  // renders real copy; the key itself is the last resort, never a blank UI.
  // This key echo is load-bearing for errors.js, which detects lookup misses.
  const t = (key, params) => {
    const active = translate(activeCatalog, key, params)
    if (active !== undefined) return active
    const fallback = translate(fallbackCatalog, key, params)
    return fallback !== undefined ? fallback : key
  }

  // List-shaped content (FAQ pairs, feature cards) keeps its order in the
  // catalog, where translators can see it. Missing lists degrade to empty.
  const tList = (key) => readList(activeCatalog, key) || readList(fallbackCatalog, key) || []

  return { t, tList }
}
