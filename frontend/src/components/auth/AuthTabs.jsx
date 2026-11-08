import { useI18n } from '../../i18n/useI18n'
import { TAB_ACTIVE, TAB_BASE, TAB_IDLE } from './auth-styles'

export default function AuthTabs({ isRegistering, onChange }) {
  const { t } = useI18n()

  return (
    <div
      className="mb-6 flex gap-2 border-b-2 border-gray-200"
      role="tablist"
      aria-label={t('auth.tablistAria')}
    >
      <button
        id="login-tab"
        type="button"
        role="tab"
        aria-selected={!isRegistering}
        aria-controls="login-panel"
        className={`${TAB_BASE} ${!isRegistering ? TAB_ACTIVE : TAB_IDLE}`}
        onClick={() => onChange('login')}
      >
        {t('auth.tabLogin')}
      </button>
      <button
        id="register-tab"
        type="button"
        role="tab"
        aria-selected={isRegistering}
        aria-controls="register-panel"
        className={`${TAB_BASE} ${isRegistering ? TAB_ACTIVE : TAB_IDLE}`}
        onClick={() => onChange('register')}
      >
        {t('auth.tabRegister')}
      </button>
    </div>
  )
}
