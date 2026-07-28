import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useAuth } from '../../context/useAuth'
import { translateApiError } from '../../i18n/errors'
import { useI18n } from '../../i18n/useI18n'
import { ApiError } from '../../services/api'
import './AuthCard.css'
import LoginForm from './LoginForm'
import RegisterForm from './RegisterForm'
import { GoogleIcon } from './AuthIcons'

const initialFormData = {
  loginIdentifier: '',
  loginPassword: '',
  rememberMe: false,
  email: '',
  username: '',
  fullName: '',
  phone: '',
  password: '',
  confirmPassword: '',
  acceptTerms: false,
}

export default function AuthCard() {
  const navigate = useNavigate()
  const { login, register } = useAuth()
  const { t } = useI18n()
  const [activeTab, setActiveTab] = useState('login')
  const [formData, setFormData] = useState(initialFormData)
  const [errors, setErrors] = useState({})
  const [showPassword, setShowPassword] = useState(false)
  const [showConfirmPassword, setShowConfirmPassword] = useState(false)
  const [isSubmitting, setIsSubmitting] = useState(false)
  const [feedback, setFeedback] = useState(null)
  const isRegistering = activeTab === 'register'

  const changeTab = (tab) => {
    setActiveTab(tab)
    setErrors({})
    setFeedback(null)
  }

  const handleChange = (event) => {
    const { name, value, type, checked } = event.target
    setFormData((current) => ({ ...current, [name]: type === 'checkbox' ? checked : value }))
    setErrors((current) => ({ ...current, [name]: '' }))
    setFeedback(null)
  }

  // These mirror the backend constraints in schemas/auth.py. The backend stays
  // the source of truth; these only save a round-trip.
  const validateLogin = () => {
    const nextErrors = {}
    if (!formData.loginIdentifier.trim()) nextErrors.loginIdentifier = 'auth.validation.identifierRequired'
    if (!formData.loginPassword) nextErrors.loginPassword = 'auth.validation.passwordRequired'
    return nextErrors
  }

  const validateRegistration = () => {
    const nextErrors = {}
    const emailPattern = /^[^\s@]+@[^\s@]+\.[^\s@]+$/
    const phonePattern = /^(0|\+84)[0-9]{8,10}$/

    if (!emailPattern.test(formData.email.trim())) nextErrors.email = 'auth.validation.emailInvalid'
    if (!/^[a-z0-9_]{3,30}$/.test(formData.username.trim().toLowerCase()))
      nextErrors.username = 'auth.validation.usernameInvalid'
    if (formData.fullName.trim().length < 2) nextErrors.fullName = 'auth.validation.fullNameRequired'
    if (formData.phone && !phonePattern.test(formData.phone.replace(/[.\s-]/g, '')))
      nextErrors.phone = 'auth.validation.phoneInvalid'
    if (formData.password.length < 8) nextErrors.password = 'auth.validation.passwordTooShort'
    if (formData.confirmPassword !== formData.password)
      nextErrors.confirmPassword = 'auth.validation.confirmMismatch'
    if (!formData.acceptTerms) nextErrors.acceptTerms = 'auth.validation.termsRequired'
    return nextErrors
  }

  const mapBackendErrors = (fields) => ({
    loginIdentifier: fields.identifier,
    loginPassword: fields.password,
    email: fields.email,
    username: fields.username,
    fullName: fields.fullName || fields.full_name,
    phone: fields.phone,
    password: fields.password,
    acceptTerms: fields.acceptTerms || fields.accept_terms,
  })

  const handleSubmit = async (event) => {
    event.preventDefault()
    const nextErrors = isRegistering ? validateRegistration() : validateLogin()

    if (Object.keys(nextErrors).length) {
      setErrors(nextErrors)
      setFeedback({ type: 'error', key: 'auth.validation.checkForm' })
      return
    }

    setErrors({})
    setFeedback(null)
    setIsSubmitting(true)

    try {
      if (isRegistering) {
        await register({
          email: formData.email.trim(),
          username: formData.username.trim().toLowerCase(),
          fullName: formData.fullName.trim(),
          phone: formData.phone || undefined,
          password: formData.password,
          acceptTerms: formData.acceptTerms,
        })
      } else {
        await login({
          identifier: formData.loginIdentifier.trim(),
          password: formData.loginPassword,
          rememberMe: formData.rememberMe,
        })
      }
      navigate('/chat')
    } catch (error) {
      const backendErrors = error instanceof ApiError ? mapBackendErrors(error.fields) : {}
      setErrors(Object.fromEntries(Object.entries(backendErrors).filter(([, message]) => message)))
      setFeedback({ type: 'error', error })
    } finally {
      setIsSubmitting(false)
    }
  }

  // Backend field errors are Vietnamese sentences, not keys. t() echoes a miss,
  // so resolving every value here handles both sources without storing copy.
  const translatedErrors = Object.fromEntries(
    Object.entries(errors).map(([field, keyOrMessage]) => [field, t(keyOrMessage)])
  )
  const feedbackMessage = feedback
    ? feedback.key
      ? t(feedback.key)
      : translateApiError(t, feedback.error)
    : ''

  const formProps = {
    formData,
    errors: translatedErrors,
    onChange: handleChange,
    showPassword,
    onTogglePassword: () => setShowPassword((value) => !value),
  }

  return (
    <section className="auth-card" aria-label={t('auth.cardAria')}>
      <div className="tabs" role="tablist" aria-label={t('auth.tablistAria')}>
        <button
          id="login-tab"
          type="button"
          role="tab"
          aria-selected={!isRegistering}
          aria-controls="login-panel"
          className={`tab ${!isRegistering ? 'active' : ''}`}
          onClick={() => changeTab('login')}
        >
          {t('auth.tabLogin')}
        </button>
        <button
          id="register-tab"
          type="button"
          role="tab"
          aria-selected={isRegistering}
          aria-controls="register-panel"
          className={`tab ${isRegistering ? 'active' : ''}`}
          onClick={() => changeTab('register')}
        >
          {t('auth.tabRegister')}
        </button>
      </div>

      <h3>{isRegistering ? t('auth.registerHeading') : t('auth.loginHeading')}</h3>
      <p className="auth-subtitle">{isRegistering ? t('auth.registerSubtitle') : t('auth.loginSubtitle')}</p>

      <form onSubmit={handleSubmit} noValidate>
        {isRegistering ? (
          <RegisterForm
            {...formProps}
            showConfirmPassword={showConfirmPassword}
            onToggleConfirmPassword={() => setShowConfirmPassword((value) => !value)}
          />
        ) : (
          <LoginForm
            {...formProps}
            onForgotPassword={() => setFeedback({ type: 'info', key: 'auth.forgotPasswordNotice' })}
          />
        )}

        {feedback && (
          <p
            className={`auth-feedback ${feedback.type}`}
            role={feedback.type === 'error' ? 'alert' : 'status'}
          >
            {feedbackMessage}
          </p>
        )}

        <button type="submit" className="primary-btn" disabled={isSubmitting}>
          {isSubmitting
            ? t('auth.submitting')
            : isRegistering
              ? t('auth.submitRegister')
              : t('auth.submitLogin')}
        </button>
        <div className="divider">
          <span>{t('auth.divider')}</span>
        </div>
        <button
          type="button"
          className="google-btn"
          onClick={() => setFeedback({ type: 'info', key: 'auth.googleNotice' })}
        >
          <GoogleIcon />
          {isRegistering ? t('auth.googleRegister') : t('auth.googleLogin')}
        </button>
      </form>
    </section>
  )
}
