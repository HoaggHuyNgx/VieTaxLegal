import './Footer.css'
import logo from '../../assets/images/logo/logo.webp'
import { useI18n } from '../../i18n/useI18n'

const CONTACT_EMAIL = 'hello@vietaxlegal.vn'

// Hrefs are structure, not copy, so they stay here and join the catalog by id.
const NAV_HREFS = {
  product: '#features',
  features: '#features',
  pricing: '#pricing',
  contact: '#contact',
  privacy: '#privacy',
}

export default function Footer() {
  const { t, tList } = useI18n()

  return (
    <footer className="footer">
      <div className="container">
        <div className="footer-main">
          <section className="footer-brand" aria-label={t('common.brandName')}>
            <div className="footer-brand-row">
              <div className="footer-logo">
                <img src={logo} alt={t('common.brandName')} />
              </div>
              <h3>{t('common.brandName')}</h3>
            </div>
            <p>{t('landing.footer.tagline')}</p>
          </section>

          <div className="footer-divider" aria-hidden="true" />

          <div className="footer-details">
            <nav className="footer-nav" aria-label={t('landing.footer.navAria')}>
              {tList('landing.footer.links').map((link) => (
                <a key={link.id} href={NAV_HREFS[link.id]}>
                  {link.label}
                </a>
              ))}
            </nav>

            <a className="footer-contact" href={`mailto:${CONTACT_EMAIL}`}>
              <svg width="18" height="18" viewBox="0 0 24 24" fill="none" aria-hidden="true">
                <rect x="3" y="5" width="18" height="14" rx="2" stroke="currentColor" strokeWidth="1.8" />
                <path
                  d="M4 7L12 13L20 7"
                  stroke="currentColor"
                  strokeWidth="1.8"
                  strokeLinecap="round"
                  strokeLinejoin="round"
                />
              </svg>
              <span>{t('landing.footer.emailLabel', { address: CONTACT_EMAIL })}</span>
            </a>
          </div>
        </div>

        <a href="#top" className="back-to-top" aria-label={t('landing.footer.backToTopAria')}>
          ↑
        </a>
      </div>
    </footer>
  )
}
