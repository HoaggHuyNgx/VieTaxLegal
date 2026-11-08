import { useI18n } from '../../i18n/useI18n'
import { FieldError } from './AuthIcons'
import { INPUT, INPUT_PADDING, LABEL, SECONDARY_BUTTON } from './auth-styles'

// Sits under the email input of the register form: request a code, enter it, get the ✓.
export default function EmailVerificationField({
  email,
  code,
  onCodeChange,
  status,
  cooldown,
  isBusy,
  errorText,
  onSend,
  onVerify,
}) {
  const { t } = useI18n()

  if (status === 'verified') {
    return (
      <p
        className="-mt-[0.4rem] mb-[1.1rem] text-[0.84rem] font-medium text-feedback-success-fg"
        role="status"
      >
        ✓ {t('auth.emailCode.verified')}
      </p>
    )
  }

  let sendLabel = t('auth.emailCode.send')
  if (isBusy && status === 'idle') sendLabel = t('auth.emailCode.sending')
  else if (cooldown > 0) sendLabel = t('auth.emailCode.resendIn', { seconds: cooldown })
  else if (status === 'sent') sendLabel = t('auth.emailCode.resend')

  return (
    <div className="-mt-[0.4rem] mb-[1.1rem]">
      <button
        type="button"
        className={SECONDARY_BUTTON}
        disabled={isBusy || cooldown > 0 || !email.trim()}
        onClick={onSend}
      >
        {sendLabel}
      </button>
      {status === 'sent' && (
        <div className="mt-3">
          <p className="mb-2 text-[0.8rem] text-auth-muted">{t('auth.emailCode.sent', { email })}</p>
          <label className={LABEL} htmlFor="email-code">
            {t('auth.emailCode.label')}
          </label>
          <div className="flex gap-2">
            <input
              id="email-code"
              className={`${INPUT} ${INPUT_PADDING}`}
              name="emailCode"
              inputMode="numeric"
              autoComplete="one-time-code"
              maxLength={6}
              placeholder={t('auth.emailCode.placeholder')}
              value={code}
              onChange={onCodeChange}
              aria-invalid={Boolean(errorText)}
              aria-describedby={errorText ? 'email-code-error' : undefined}
            />
            <button
              type="button"
              className={SECONDARY_BUTTON}
              disabled={isBusy || code.length !== 6}
              onClick={onVerify}
            >
              {isBusy ? t('auth.emailCode.verifying') : t('auth.emailCode.verify')}
            </button>
          </div>
        </div>
      )}
      <FieldError error={errorText} id="email-code-error" />
    </div>
  )
}
