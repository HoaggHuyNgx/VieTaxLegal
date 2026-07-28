import en from './locales/en'
import vi from './locales/vi'

export const DEFAULT_LOCALE = 'vi'
export const SUPPORTED_LOCALES = ['vi', 'en']

// Intl tags for time formatting, keyed by app locale.
export const LOCALE_TAGS = { vi: 'vi-VN', en: 'en-US' }

const catalogs = { vi, en }

export function catalogFor(locale) {
  return catalogs[locale] || catalogs[DEFAULT_LOCALE]
}

export function localeTagFor(locale) {
  return LOCALE_TAGS[locale] || LOCALE_TAGS[DEFAULT_LOCALE]
}

export function isSupportedLocale(value) {
  return SUPPORTED_LOCALES.includes(value)
}
