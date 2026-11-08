import { useI18n } from '../../i18n/useI18n'
import { EyeIcon, FieldError } from './AuthIcons'
import EmailVerificationField from './EmailVerificationField'
import PasswordChecklist from './PasswordChecklist'
import {
  CHECKBOX_INPUT,
  CHECKBOX_LABEL,
  FIELD_GROUP,
  INPUT,
  INPUT_PADDING,
  INPUT_PADDING_PASSWORD,
  LABEL,
  OPTIONAL_MARK,
  REQUIRED_MARK,
  TERMS_LABEL,
  TERMS_LINK,
  TOGGLE_PASSWORD,
} from './auth-styles'

export default function RegisterForm({
  formData,
  errors,
  onChange,
  showPassword,
  onTogglePassword,
  showConfirmPassword,
  onToggleConfirmPassword,
  verification,
}) {
  const { t } = useI18n()

  return (
    <div id="register-panel" role="tabpanel" aria-labelledby="register-tab">
      <div className={FIELD_GROUP}>
        <label className={LABEL} htmlFor="register-email">
          {t('auth.fields.email')} <span className={REQUIRED_MARK}>*</span>
        </label>
        <input
          id="register-email"
          className={`${INPUT} ${INPUT_PADDING}`}
          name="email"
          type="email"
          autoComplete="email"
          placeholder={t('auth.fields.emailPlaceholder')}
          value={formData.email}
          onChange={onChange}
          readOnly={verification.status === 'verified'}
          aria-invalid={Boolean(errors.email)}
          aria-describedby={errors.email ? 'register-email-error' : undefined}
        />
        <FieldError error={errors.email} id="register-email-error" />
      </div>
      <EmailVerificationField
        email={formData.email}
        code={formData.emailCode}
        onCodeChange={onChange}
        {...verification}
      />
      <div className={FIELD_GROUP}>
        <label className={LABEL} htmlFor="username">
          {t('auth.fields.username')} <span className={REQUIRED_MARK}>*</span>
        </label>
        <input
          id="username"
          className={`${INPUT} ${INPUT_PADDING}`}
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
      <div className={FIELD_GROUP}>
        <label className={LABEL} htmlFor="full-name">
          {t('auth.fields.fullName')} <span className={REQUIRED_MARK}>*</span>
        </label>
        <input
          id="full-name"
          className={`${INPUT} ${INPUT_PADDING}`}
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
      <div className={FIELD_GROUP}>
        <label className={LABEL} htmlFor="phone">
          {t('auth.fields.phone')} <span className={OPTIONAL_MARK}>{t('auth.fields.phoneOptional')}</span>
        </label>
        <input
          id="phone"
          className={`${INPUT} ${INPUT_PADDING}`}
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
      <div className={FIELD_GROUP}>
        <label className={LABEL} htmlFor="register-password">
          {t('auth.fields.password')} <span className={REQUIRED_MARK}>*</span>
        </label>
        <div className="relative">
          <input
            id="register-password"
            className={`${INPUT} ${INPUT_PADDING_PASSWORD}`}
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
            className={TOGGLE_PASSWORD}
            onClick={onTogglePassword}
            aria-label={showPassword ? t('auth.fields.hidePasswordAria') : t('auth.fields.showPasswordAria')}
          >
            <EyeIcon hidden={showPassword} />
          </button>
        </div>
        <FieldError error={errors.password} id="register-password-error" />
        <PasswordChecklist password={formData.password} email={formData.email} username={formData.username} />
      </div>
      <div className={FIELD_GROUP}>
        <label className={LABEL} htmlFor="confirm-password">
          {t('auth.fields.confirmPassword')} <span className={REQUIRED_MARK}>*</span>
        </label>
        <div className="relative">
          <input
            id="confirm-password"
            className={`${INPUT} ${INPUT_PADDING_PASSWORD}`}
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
            className={TOGGLE_PASSWORD}
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
      <label className={`${CHECKBOX_LABEL} ${TERMS_LABEL}`}>
        <input
          className={CHECKBOX_INPUT}
          type="checkbox"
          name="acceptTerms"
          checked={formData.acceptTerms}
          onChange={onChange}
          aria-invalid={Boolean(errors.acceptTerms)}
          aria-describedby={errors.acceptTerms ? 'accept-terms-error' : undefined}
        />
        <span>
          {t('auth.terms.prefix')}
          <a className={TERMS_LINK} href="#terms">
            {t('auth.terms.termsLink')}
          </a>
          {t('auth.terms.middle')}
          <a className={TERMS_LINK} href="#privacy">
            {t('auth.terms.privacyLink')}
          </a>
          {t('auth.terms.suffix')}
        </span>
      </label>
      <FieldError error={errors.acceptTerms} id="accept-terms-error" />
    </div>
  )
}
