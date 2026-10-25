import heroBackground from '../../assets/images/backgrounds/auth-background.webp'
import logo from '../../assets/images/logo/logo.webp'
import AuthCard from '../auth/AuthCard'
import LanguageToggle from '../common/LanguageToggle'
import { useI18n } from '../../i18n/useI18n'

function CheckIcon() {
  return (
    <svg
      className="mt-0.5 shrink-0 opacity-90"
      width="20"
      height="20"
      viewBox="0 0 20 20"
      fill="currentColor"
      aria-hidden="true"
    >
      <path
        fillRule="evenodd"
        d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z"
        clipRule="evenodd"
      />
    </svg>
  )
}

export default function Hero() {
  const { t, tList } = useI18n()

  return (
    <header className="relative min-h-screen overflow-hidden bg-blue-deep py-8 text-white lte-968:pb-12">
      <div
        className="absolute inset-0 bg-bottom bg-no-repeat bg-cover opacity-60"
        style={{ backgroundImage: `url(${heroBackground})` }}
      />

      <div className="relative z-2 flex justify-end px-8 lte-968:px-4">
        <LanguageToggle />
      </div>

      <div className="relative z-1 px-8 pt-12 pb-8 text-center lte-968:px-4 lte-968:pt-8 lte-968:pb-4">
        <div className="mb-6 flex items-center justify-center gap-6 lte-640:mb-4 lte-640:gap-3">
          <div className="inline-flex">
            <img className="h-auto w-18 lte-640:w-12" src={logo} alt={t('common.brandName')} />
          </div>
          <h1 className="m-0 text-[3.5rem] leading-none font-bold lte-968:text-[2rem]">
            {t('common.brandName')}
          </h1>
        </div>
        <p className="mb-3 text-[1.25rem] font-semibold opacity-95 lte-640:text-[1.05rem]">
          {t('landing.hero.tagline')}
        </p>
        {/* No <br />: a break tuned to the Vietnamese line length falls in the
            wrong place in English, so max-width owns the wrap. */}
        <p className="mx-auto max-w-[37.5rem] text-[1rem] leading-[1.6] opacity-85 lte-640:text-[0.9rem]">
          {t('landing.hero.description')}
        </p>
      </div>

      <div className="relative z-1 mx-auto grid max-w-[1280px] grid-cols-[minmax(0,1fr)_minmax(0,1fr)] [align-items:start] gap-12 px-8 lte-968:grid-cols-[1fr] lte-968:gap-8 lte-768:px-4">
        <section className="pt-6 lte-968:pt-0 lte-968:text-center">
          <h2 className="mb-6 text-[2rem] font-bold">{t('common.brandName')}</h2>
          <ul className="flex list-none flex-col gap-4 lte-968:mx-auto lte-968:max-w-[38rem]">
            {tList('landing.hero.benefits').map((benefit) => (
              <li
                key={benefit.id}
                className="flex items-start gap-3 text-[0.95rem] leading-[1.6] lte-968:text-left"
              >
                <CheckIcon />
                {benefit.text}
              </li>
            ))}
          </ul>
        </section>

        <AuthCard />
      </div>
    </header>
  )
}
