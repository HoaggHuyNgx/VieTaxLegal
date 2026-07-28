import { SUPPORTED_LOCALES } from '../../i18n/catalogs'
import { useI18n } from '../../i18n/useI18n'
import './LanguageToggle.css'

const LOCALE_SHORT = { vi: 'VI', en: 'EN' }
const LOCALE_NAME_KEY = { vi: 'common.localeVi', en: 'common.localeEn' }

export default function LanguageToggle() {
  const { locale, setLocale, t } = useI18n()

  return (
    <div className="language-toggle" role="group" aria-label={t('common.languageLabel')}>
      {SUPPORTED_LOCALES.map((item) => (
        <button
          key={item}
          type="button"
          className={`language-option ${item === locale ? 'active' : ''}`}
          aria-pressed={item === locale}
          onClick={() => setLocale(item)}
        >
          <span>{LOCALE_SHORT[item]}</span>{' '}
          <span className="language-option-name">{t(LOCALE_NAME_KEY[item])}</span>
        </button>
      ))}
    </div>
  )
}
