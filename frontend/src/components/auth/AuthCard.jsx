import { useEffect, useState } from 'react'
import { useNavigate, useSearchParams } from 'react-router-dom'
import { useAuth } from '../../context/useAuth'
import { translateApiError } from '../../i18n/errors'
import { useI18n } from '../../i18n/useI18n'
import { ApiError } from '../../services/api'
import AuthTabs from './AuthTabs'
import GoogleSignInButton from './GoogleSignInButton'
import LoginForm from './LoginForm'
import RegisterForm from './RegisterForm'
import { EMAIL_PATTERN, mapBackendErrors, validateLogin, validateRegistration } from './auth-validation'
import { DIVIDER, FEEDBACK, FEEDBACK_TONE, PRIMARY_BUTTON } from './auth-styles'
import { useEmailVerification } from './useEmailVerification'

const initialFormData = {
  loginIdentifier: '',
  loginPassword: '',
  rememberMe: false,
  email: '',
  emailCode: '',
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
  // The Google callback sends the browser back to `/?authError=CODE` when it is refused.
  const [searchParams, setSearchParams] = useSearchParams()
  const [feedback, setFeedback] = useState(() => {
    const code = searchParams.get('authError')
    return code ? { type: 'error', error: { code } } : null
  })
  const emailVerification = useEmailVerification()
  const isRegistering = activeTab === 'register'
  const normalizedEmail = formData.email.trim().toLowerCase()

  useEffect(() => {
    if (!searchParams.has('authError')) return
    const next = new URLSearchParams(searchParams)
    next.delete('authError')
    setSearchParams(next, { replace: true })
  }, [searchParams, setSearchParams])

  const changeTab = (tab) => {
    setActiveTab(tab)
    setErrors({})
    setFeedback(null)
  }

  const handleChange = (event) => {
    const { name, value, type, checked } = event.target
    // The code input only takes digits; a code belongs to one address, so editing the
    // email discards any code requested for the old one.
    const nextValue = name === 'emailCode' ? value.replace(/\D/g, '') : value
    if (name === 'email' && emailVerification.status === 'sent') emailVerification.reset()
    setFormData((current) => ({ ...current, [name]: type === 'checkbox' ? checked : nextValue }))
    setErrors((current) => ({ ...current, [name]: '' }))
    setFeedback(null)
  }

  const handleSendCode = () => {
    if (!EMAIL_PATTERN.test(normalizedEmail)) {
      setErrors((current) => ({ ...current, email: 'auth.validation.emailInvalid' }))
      return
    }
    emailVerification.sendCode(normalizedEmail)
  }

  const handleSubmit = async (event) => {
    event.preventDefault()
    const nextErrors = isRegistering
      ? validateRegistration(formData, emailVerification.status === 'verified')
      : validateLogin(formData)

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
          emailProof: emailVerification.proof,
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
      setErrors(error instanceof ApiError ? mapBackendErrors(error.fields) : {})
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
    <section
      className="w-full rounded-[1.25rem] bg-white p-8 text-gray-900 shadow-auth-card lte-640:rounded-2xl lte-640:p-6"
      aria-label={t('auth.cardAria')}
    >
      <AuthTabs isRegistering={isRegistering} onChange={changeTab} />

      <h3 className="mb-2 text-[1.35rem] leading-[1.3] font-bold text-gray-900 lte-640:text-[1.2rem]">
        {isRegistering ? t('auth.registerHeading') : t('auth.loginHeading')}
      </h3>
      <p className="mb-6 text-[0.9rem] text-gray-700">
        {isRegistering ? t('auth.registerSubtitle') : t('auth.loginSubtitle')}
      </p>

      <form onSubmit={handleSubmit} noValidate>
        {isRegistering ? (
          <RegisterForm
            {...formProps}
            showConfirmPassword={showConfirmPassword}
            onToggleConfirmPassword={() => setShowConfirmPassword((value) => !value)}
            verification={{
              status: emailVerification.status,
              cooldown: emailVerification.cooldown,
              isBusy: emailVerification.isBusy,
              errorText: emailVerification.error ? translateApiError(t, emailVerification.error) : '',
              onSend: handleSendCode,
              onVerify: () => emailVerification.verifyCode(normalizedEmail, formData.emailCode),
            }}
          />
        ) : (
          <LoginForm
            {...formProps}
            onForgotPassword={() => setFeedback({ type: 'info', key: 'auth.forgotPasswordNotice' })}
          />
        )}

        {feedback && (
          <p
            className={`${FEEDBACK} ${FEEDBACK_TONE[feedback.type]}`}
            role={feedback.type === 'error' ? 'alert' : 'status'}
          >
            {feedbackMessage}
          </p>
        )}

        <button type="submit" className={PRIMARY_BUTTON} disabled={isSubmitting}>
          {isSubmitting
            ? t('auth.submitting')
            : isRegistering
              ? t('auth.submitRegister')
              : t('auth.submitLogin')}
        </button>
        <div className={DIVIDER}>
          <span className="px-4">{t('auth.divider')}</span>
        </div>
        <GoogleSignInButton isRegistering={isRegistering} />
      </form>
    </section>
  )
}
