import { useI18n } from '../../i18n/useI18n'
import { EyeIcon, FieldError } from './AuthIcons'

export default function RegisterForm({
  formData,
  errors,
  onChange,
  showPassword,
  onTogglePassword,
  showConfirmPassword,
  onToggleConfirmPassword,
}) {
  const { t } = useI18n()

  return (
    <div id="register-panel" className="register-fields" role="tabpanel" aria-labelledby="register-tab">
      <div className="form-group">
        <label htmlFor="register-email">
          {t('auth.fields.email')} <span className="required-mark">*</span>
        </label>
        <input
          id="register-email"
          name="email"
          type="email"
          autoComplete="email"
          placeholder={t('auth.fields.emailPlaceholder')}
          value={formData.email}
          onChange={onChange}
          aria-invalid={Boolean(errors.email)}
          aria-describedby={errors.email ? 'register-email-error' : undefined}
        />
        <FieldError error={errors.email} id="register-email-error" />
      </div>
      <div className="form-group">
        <label htmlFor="username">
          {t('auth.fields.username')} <span className="required-mark">*</span>
        </label>
        <input
          id="username"
          name="username"
          type="text"
          autoComplete="username"
          placeholder={t('auth.fields.usernamePlaceholder')}
          value={formData.username}
          onChange={onChange}
          aria-invalid={Boolean(errors.username)}
          aria-describedby={errors.username ? 'username-error' : undefined}
        />
        <FieldError error={errors.username} id="username-error" />
      </div>
      <div className="form-group">
        <label htmlFor="full-name">
          {t('auth.fields.fullName')} <span className="required-mark">*</span>
        </label>
        <input
          id="full-name"
          name="fullName"
          type="text"
          autoComplete="name"
          placeholder={t('auth.fields.fullNamePlaceholder')}
          value={formData.fullName}
          onChange={onChange}
          aria-invalid={Boolean(errors.fullName)}
          aria-describedby={errors.fullName ? 'full-name-error' : undefined}
        />
        <FieldError error={errors.fullName} id="full-name-error" />
      </div>
      <div className="form-group">
        <label htmlFor="phone">
          {t('auth.fields.phone')} <span className="optional-mark">{t('auth.fields.phoneOptional')}</span>
        </label>
        <input
          id="phone"
          name="phone"
          type="tel"
          inputMode="tel"
          autoComplete="tel"
          placeholder={t('auth.fields.phonePlaceholder')}
          value={formData.phone}
          onChange={onChange}
          aria-invalid={Boolean(errors.phone)}
          aria-describedby={errors.phone ? 'phone-error' : undefined}
        />
        <FieldError error={errors.phone} id="phone-error" />
      </div>
      <div className="form-group">
        <label htmlFor="register-password">
          {t('auth.fields.password')} <span className="required-mark">*</span>
        </label>
        <div className="password-input">
          <input
            id="register-password"
            name="password"
            type={showPassword ? 'text' : 'password'}
            autoComplete="new-password"
            placeholder={t('auth.fields.newPasswordPlaceholder')}
            value={formData.password}
            onChange={onChange}
            aria-invalid={Boolean(errors.password)}
            aria-describedby={errors.password ? 'register-password-error' : undefined}
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
        <FieldError error={errors.password} id="register-password-error" />
      </div>
      <div className="form-group">
        <label htmlFor="confirm-password">
          {t('auth.fields.confirmPassword')} <span className="required-mark">*</span>
        </label>
        <div className="password-input">
          <input
            id="confirm-password"
            name="confirmPassword"
            type={showConfirmPassword ? 'text' : 'password'}
            autoComplete="new-password"
            placeholder={t('auth.fields.confirmPasswordPlaceholder')}
            value={formData.confirmPassword}
            onChange={onChange}
            aria-invalid={Boolean(errors.confirmPassword)}
            aria-describedby={errors.confirmPassword ? 'confirm-password-error' : undefined}
          />
          <button
            type="button"
            className="toggle-password"
            onClick={onToggleConfirmPassword}
            aria-label={
              showConfirmPassword
                ? t('auth.fields.hideConfirmPasswordAria')
                : t('auth.fields.showConfirmPasswordAria')
            }
          >
            <EyeIcon hidden={showConfirmPassword} />
          </button>
        </div>
        <FieldError error={errors.confirmPassword} id="confirm-password-error" />
      </div>
      <label className="checkbox-label terms-label">
        <input
          type="checkbox"
          name="acceptTerms"
          checked={formData.acceptTerms}
          onChange={onChange}
          aria-invalid={Boolean(errors.acceptTerms)}
          aria-describedby={errors.acceptTerms ? 'accept-terms-error' : undefined}
        />
        <span>
          {t('auth.terms.prefix')}
          <a href="#terms">{t('auth.terms.termsLink')}</a>
          {t('auth.terms.middle')}
          <a href="#privacy">{t('auth.terms.privacyLink')}</a>
          {t('auth.terms.suffix')}
        </span>
      </label>
      <FieldError error={errors.acceptTerms} id="accept-terms-error" />
    </div>
  )
}
