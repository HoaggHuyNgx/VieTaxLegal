import { useI18n } from '../../i18n/useI18n'
import { EyeIcon, FieldError } from './AuthIcons'

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
      <div className="form-group">
        <label htmlFor="login-identifier">{t('auth.fields.identifier')}</label>
        <input
          id="login-identifier"
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
      <div className="form-group">
        <label htmlFor="login-password">{t('auth.fields.password')}</label>
        <div className="password-input">
          <input
            id="login-password"
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
            className="toggle-password"
            onClick={onTogglePassword}
            aria-label={showPassword ? t('auth.fields.hidePasswordAria') : t('auth.fields.showPasswordAria')}
          >
            <EyeIcon hidden={showPassword} />
          </button>
        </div>
        <FieldError error={errors.loginPassword} id="login-password-error" />
      </div>
      <div className="form-row">
        <label className="checkbox-label">
          <input type="checkbox" name="rememberMe" checked={formData.rememberMe} onChange={onChange} />
          {t('auth.fields.rememberMe')}
        </label>
        <button type="button" className="forgot-link" onClick={onForgotPassword}>
          {t('auth.fields.forgotPassword')}
        </button>
      </div>
    </div>
  )
}
