import { useState } from 'react'
import { Link, useSearchParams } from 'react-router-dom'
import LanguageToggle from '../components/common/LanguageToggle'
import { useAuth } from '../context/useAuth'
import { translateApiError } from '../i18n/errors'
import { useI18n } from '../i18n/useI18n'
import { getCurrentUser, googleAuthUrl } from '../services/auth'

const CARD = 'rounded-chat-lg border border-chat-border bg-chat-surface p-5 shadow-chat-soft'
const LINK_BUTTON =
  'cursor-pointer rounded-chat-sm border border-chat-blue bg-chat-blue px-4 py-2 text-[13px] font-semibold text-white focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-chat-blue disabled:cursor-wait disabled:opacity-60'

export default function SettingsPage() {
  const { t } = useI18n()
  const { user } = useAuth()
  const [searchParams] = useSearchParams()
  const [isLinking, setIsLinking] = useState(false)
  const [linkError, setLinkError] = useState(null)

  // The callback returns here as `?google=linked` or `?authError=CODE`.
  const urlErrorCode = searchParams.get('authError')
  const error = linkError || (urlErrorCode ? { code: urlErrorCode } : null)
  const justLinked = searchParams.get('google') === 'linked'

  const startLinking = async () => {
    setIsLinking(true)
    setLinkError(null)
    try {
      // The redirect is a plain page load, so renew an expired access cookie first.
      await getCurrentUser()
      window.location.assign(googleAuthUrl('link'))
    } catch (requestError) {
      setLinkError(requestError)
      setIsLinking(false)
    }
  }

  return (
    <main className="min-h-dvh bg-chat-canvas p-[26px_30px] text-[14px] text-chat-ink lte-760:p-[19px_15px]">
      <div className="mx-auto max-w-[640px]">
        <header className="mb-5 flex items-start justify-between gap-4">
          <div>
            <h1 className="m-0 text-[21px] font-[750] tracking-[-0.55px]">{t('settings.title')}</h1>
            <p className="mt-1 text-[12px] text-chat-muted">{user?.email}</p>
          </div>
          <div className="flex items-center gap-3">
            <Link to="/chat" className="text-[13px] font-medium text-chat-blue no-underline hover:underline">
              {t('settings.backToChat')}
            </Link>
            <LanguageToggle />
          </div>
        </header>

        {error ? (
          <p
            role="alert"
            className="mb-4 rounded-chat border border-chat-danger bg-chat-danger-soft px-4 py-3 text-chat-danger"
          >
            {translateApiError(t, error)}
          </p>
        ) : null}
        {justLinked && !error ? (
          <p role="status" className="mb-4 rounded-chat bg-tint-green-bg px-4 py-3 text-tint-green-fg">
            {t('settings.google.justLinked')}
          </p>
        ) : null}

        <section className={CARD} aria-labelledby="google-heading">
          <h2 id="google-heading" className="m-0 text-[15px] font-bold">
            {t('settings.google.title')}
          </h2>
          <p className="mt-1 mb-4 text-[13px] text-chat-muted">{t('settings.google.description')}</p>
          {user?.googleLinked ? (
            <span className="rounded-chat-pill bg-tint-green-bg px-[9px] py-[3px] text-[11px] font-bold text-tint-green-fg">
              {t('settings.google.linked')}
            </span>
          ) : (
            <button type="button" className={LINK_BUTTON} disabled={isLinking} onClick={startLinking}>
              {isLinking ? t('settings.google.linking') : t('settings.google.link')}
            </button>
          )}
        </section>
      </div>
    </main>
  )
}
