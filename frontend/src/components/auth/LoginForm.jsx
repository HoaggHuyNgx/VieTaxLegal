import { useI18n } from '../../i18n/useI18n'
import { EyeIcon, FieldError } from './AuthIcons'
import {
  CHECKBOX_INPUT,
  CHECKBOX_LABEL,
  FIELD_GROUP,
  FORGOT_LINK,
  INPUT,
  INPUT_PADDING,
  INPUT_PADDING_PASSWORD,
  LABEL,
  TOGGLE_PASSWORD,
} from './auth-styles'

export default function LoginForm({
  formData,
  errors,
  onChange,
  showPassword,
  onTogglePassword,
  onForgotPassword,
}) {
  const { t } = useI18n()

  return (
    <div id="login-panel" role="tabpanel" aria-labelledby="login-tab">
      <div className={FIELD_GROUP}>
        <label className={LABEL} htmlFor="login-identifier">
          {t('auth.fields.identifier')}
        </label>
        <input
          id="login-identifier"
          className={`${INPUT} ${INPUT_PADDING}`}
          name="loginIdentifier"
          type="text"
          autoComplete="username"
          placeholder={t('auth.fields.identifierPlaceholder')}
          value={formData.loginIdentifier}
          onChange={onChange}
          aria-invalid={Boolean(errors.loginIdentifier)}
          aria-describedby={errors.loginIdentifier ? 'login-identifier-error' : undefined}
        />
        <FieldError error={errors.loginIdentifier} id="login-identifier-error" />
      </div>
      <div className={FIELD_GROUP}>
        <label className={LABEL} htmlFor="login-password">
          {t('auth.fields.password')}
        </label>
        <div className="relative">
          <input
            id="login-password"
            className={`${INPUT} ${INPUT_PADDING_PASSWORD}`}
            name="loginPassword"
            type={showPassword ? 'text' : 'password'}
            autoComplete="current-password"
            placeholder={t('auth.fields.passwordPlaceholder')}
            value={formData.loginPassword}
            onChange={onChange}
            aria-invalid={Boolean(errors.loginPassword)}
            aria-describedby={errors.loginPassword ? 'login-password-error' : undefined}
          />
          <button
            type="button"
            className={TOGGLE_PASSWORD}
            onClick={onTogglePassword}
            aria-label={showPassword ? t('auth.fields.hidePasswordAria') : t('auth.fields.showPasswordAria')}
          >
            <EyeIcon hidden={showPassword} />
          </button>
        </div>
        <FieldError error={errors.loginPassword} id="login-password-error" />
      </div>
      <div className="mb-5 flex items-center justify-between gap-4 text-[0.875rem] lte-640:flex-col lte-640:items-start lte-640:gap-3">
        <label className={CHECKBOX_LABEL}>
          <input
            className={CHECKBOX_INPUT}
            type="checkbox"
            name="rememberMe"
            checked={formData.rememberMe}
            onChange={onChange}
          />
          {t('auth.fields.rememberMe')}
        </label>
        <button type="button" className={FORGOT_LINK} onClick={onForgotPassword}>
          {t('auth.fields.forgotPassword')}
        </button>
      </div>
    </div>
  )
}
