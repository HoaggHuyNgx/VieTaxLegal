import { DEFAULT_LOCALE, isSupportedLocale } from './catalogs'

export const LOCALE_STORAGE_KEY = 'vietaxlegal.locale'

// Storage throws in private mode and is absent in the node test environment,
// so both directions are best-effort.
//
// Deliberately no navigator.language sniffing: many Vietnamese users run an
// English system locale, and sniffing would drop them into the wrong UI. The
// default is Vietnamese unless the user has explicitly chosen otherwise.
export function readStoredLocale() {
  try {
    const stored = globalThis.localStorage?.getItem(LOCALE_STORAGE_KEY)
    return isSupportedLocale(stored) ? stored : DEFAULT_LOCALE
  } catch {
    return DEFAULT_LOCALE
  }
}

export function storeLocale(locale) {
  try {
    globalThis.localStorage?.setItem(LOCALE_STORAGE_KEY, locale)
  } catch {
    // Persisting failed; the switch still applies for this session.
  }
}
