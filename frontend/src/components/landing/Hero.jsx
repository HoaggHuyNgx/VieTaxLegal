import './Hero.css'
import logo from '../../assets/images/logo/logo.webp'
import AuthCard from '../auth/AuthCard'
import LanguageToggle from '../common/LanguageToggle'
import { useI18n } from '../../i18n/useI18n'

function CheckIcon() {
  return (
    <svg width="20" height="20" viewBox="0 0 20 20" fill="currentColor" aria-hidden="true">
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
    <header className="hero">
      <div className="hero-background" />

      <div className="hero-toolbar">
        <LanguageToggle />
      </div>

      <div className="brand-center">
        <div className="brand-logo-wrapper">
          <div className="brand-logo">
            <img src={logo} alt={t('common.brandName')} />
          </div>
          <h1 className="brand-name">{t('common.brandName')}</h1>
        </div>
        <p className="brand-tagline">{t('landing.hero.tagline')}</p>
        {/* No <br />: a break tuned to the Vietnamese line length falls in the
            wrong place in English, so CSS max-width owns the wrap. */}
        <p className="brand-description">{t('landing.hero.description')}</p>
      </div>

      <div className="container hero-content">
        <section className="hero-copy">
          <h2>{t('common.brandName')}</h2>
          <ul className="benefit-list">
            {tList('landing.hero.benefits').map((benefit) => (
              <li key={benefit.id}>
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
