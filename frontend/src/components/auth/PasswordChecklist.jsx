import { useI18n } from '../../i18n/useI18n'
import { passwordRules } from './password-rules'

// Shown under the new-password input: each rule ticks off as the user types, so nobody has to
// guess what "strong enough" means or wait for an error after pressing submit.
export default function PasswordChecklist({ password, email, username }) {
  const { t } = useI18n()
  const rules = passwordRules(password, { email, username })

  return (
    <ul
      className="mt-[0.55rem] mb-0 grid list-none gap-[0.2rem] p-0 text-[0.8rem]"
      aria-label={t('auth.passwordRules.aria')}
    >
      {rules.map(({ id, ok }) => (
        <li
          key={id}
          className={`flex items-center gap-[0.4rem] ${ok ? 'text-feedback-success-fg' : 'text-auth-muted'}`}
        >
          <span aria-hidden="true">{ok ? '✓' : '○'}</span>
          <span>{t(`auth.passwordRules.${id}`)}</span>
          <span className="sr-only">{ok ? t('auth.passwordRules.met') : t('auth.passwordRules.unmet')}</span>
        </li>
      ))}
    </ul>
  )
}
