import { SUPPORTED_LOCALES } from '../../i18n/catalogs'
import { useI18n } from '../../i18n/useI18n'

const LOCALE_SHORT = { vi: 'VI', en: 'EN' }
const LOCALE_NAME_KEY = { vi: 'common.localeVi', en: 'common.localeEn' }

// `language-toggle` and `language-option` carry no styles here: ChatTopbar restyles
// them by these names (and the visual-regression helper clicks them).
const OPTION_BASE =
  'language-option min-w-9 rounded-[999px] border-none px-2 py-1 [font-family:inherit] text-[0.75rem] font-semibold tracking-[0.02em] cursor-pointer transition-[background,color] duration-150 ease-[ease] focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-blue-bright'
const OPTION_ACTIVE = 'active bg-blue-primary text-white'
const OPTION_IDLE = 'bg-transparent text-gray-700 hover:bg-gray-100'

export default function LanguageToggle() {
  const { locale, setLocale, t } = useI18n()

  return (
    <div
      className="language-toggle inline-flex items-center gap-0.5 rounded-[999px] border border-gray-200 bg-white p-0.5"
      role="group"
      aria-label={t('common.languageLabel')}
    >
      {SUPPORTED_LOCALES.map((item) => (
        <button
          key={item}
          type="button"
          className={`${OPTION_BASE} ${item === locale ? OPTION_ACTIVE : OPTION_IDLE}`}
          aria-pressed={item === locale}
          onClick={() => setLocale(item)}
        >
          <span>{LOCALE_SHORT[item]}</span> <span className="sr-only">{t(LOCALE_NAME_KEY[item])}</span>
        </button>
      ))}
    </div>
  )
}
