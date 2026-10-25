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
    <footer className="relative bg-blue-deep py-6 text-white lte-768:pt-8 lte-768:pb-20">
      <div className="relative mx-auto max-w-[1280px] px-8 lte-768:px-4">
        <div className="flex min-h-20 items-center gap-12 pr-[5.5rem] lte-1024:gap-8 lte-768:flex-col lte-768:gap-6 lte-768:pr-0 lte-768:text-center">
          <section
            className="flex-[0_0_16rem] lte-1024:basis-56 lte-768:basis-auto"
            aria-label={t('common.brandName')}
          >
            <div className="mb-[0.4rem] flex items-center gap-3 lte-768:justify-center">
              <div className="inline-flex">
                <img className="size-11 object-contain" src={logo} alt={t('common.brandName')} />
              </div>
              <h3 className="m-0 text-[1.5rem] leading-none font-bold">{t('common.brandName')}</h3>
            </div>
            <p className="m-0 text-[0.8rem] leading-[1.45] text-footer-muted">
              {t('landing.footer.tagline')}
            </p>
          </section>

          <div
            className="min-h-[3.25rem] w-px self-stretch bg-footer-line lte-768:h-px lte-768:min-h-px lte-768:w-16"
            aria-hidden="true"
          />

          <div className="flex min-w-0 flex-1 flex-col gap-[0.65rem] lte-768:items-center">
            <nav
              className="flex flex-wrap items-center gap-y-[0.35rem] lte-768:max-w-80 lte-768:justify-center"
              aria-label={t('landing.footer.navAria')}
            >
              {tList('landing.footer.links').map((link) => (
                <a
                  key={link.id}
                  href={NAV_HREFS[link.id]}
                  className="inline-flex items-center text-[0.82rem] leading-none font-medium whitespace-nowrap text-white no-underline transition-opacity duration-200 ease-[ease] after:mx-[0.8rem] after:text-footer-sep after:content-['|'] last:after:content-none hover:opacity-75"
                >
                  {link.label}
                </a>
              ))}
            </nav>

            <a
              className="inline-flex w-fit items-center gap-[0.55rem] text-[0.82rem] leading-none text-footer-contact no-underline transition-opacity duration-200 ease-[ease] hover:opacity-75 lte-768:justify-center"
              href={`mailto:${CONTACT_EMAIL}`}
            >
              <svg
                className="flex-none"
                width="18"
                height="18"
                viewBox="0 0 24 24"
                fill="none"
                aria-hidden="true"
              >
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

        <a
          href="#top"
          className="absolute top-1/2 right-8 flex size-12 [transform:translateY(-50%)] items-center justify-center rounded-[50%] bg-white text-[1.5rem] leading-none font-medium text-blue-deep no-underline shadow-back-to-top transition-[transform,box-shadow] duration-200 ease-[ease] hover:[transform:translateY(calc(-50%_-_3px))] hover:shadow-back-to-top-hover lte-768:top-auto lte-768:right-4 lte-768:bottom-4 lte-768:[transform:none] lte-768:hover:[transform:translateY(-3px)]"
          aria-label={t('landing.footer.backToTopAria')}
        >
          ↑
        </a>
      </div>
    </footer>
  )
}
