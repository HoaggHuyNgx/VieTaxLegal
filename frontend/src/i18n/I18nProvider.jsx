import { useCallback, useEffect, useMemo, useState } from 'react'
import { isSupportedLocale, localeTagFor } from './catalogs'
import { readStoredLocale, storeLocale } from './storage'
import { createTranslator } from './translator'
import I18nContext from './i18n-context'

export function I18nProvider({ children }) {
  const [locale, setLocaleState] = useState(readStoredLocale)
  const { t, tList } = useMemo(() => createTranslator(locale), [locale])

  useEffect(() => {
    document.documentElement.lang = locale
    document.title = t('common.pageTitle')
    const description = document.querySelector('meta[name="description"]')
    if (description) description.setAttribute('content', t('common.pageDescription'))
  }, [locale, t])

  const setLocale = useCallback((next) => {
    if (!isSupportedLocale(next)) return
    setLocaleState(next)
    storeLocale(next)
  }, [])

  const value = useMemo(
    () => ({ locale, setLocale, t, tList, localeTag: localeTagFor(locale) }),
    [locale, setLocale, t, tList]
  )

  return <I18nContext.Provider value={value}>{children}</I18nContext.Provider>
}
