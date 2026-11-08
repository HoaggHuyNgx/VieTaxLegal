import { useI18n } from '../../i18n/useI18n'
import { googleAuthUrl } from '../../services/auth'
import { GoogleIcon } from './AuthIcons'
import { GOOGLE_BUTTON } from './auth-styles'

// A full-page redirect: the backend runs the whole Google flow and sends the browser back.
export default function GoogleSignInButton({ isRegistering }) {
  const { t } = useI18n()

  return (
    <>
      <button
        type="button"
        className={GOOGLE_BUTTON}
        onClick={() => window.location.assign(googleAuthUrl('login'))}
      >
        <GoogleIcon />
        {isRegistering ? t('auth.googleRegister') : t('auth.googleLogin')}
      </button>
      <p className="mt-3 text-center text-[0.78rem] leading-[1.4] text-auth-muted">
        {t('auth.googleTermsNote')}
      </p>
    </>
  )
}
