import { useState } from 'react'
import './AuthCard.css'
import LoginForm from './LoginForm'
import RegisterForm from './RegisterForm'
import { GoogleIcon } from './AuthIcons'

const initialFormData = {
  loginIdentifier: '',
  loginPassword: '',
  rememberMe: false,
  email: '',
  fullName: '',
  phone: '',
  password: '',
  confirmPassword: '',
  acceptTerms: false,
}

export default function AuthCard() {
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

  const validateLogin = () => {
    const nextErrors = {}
    if (!formData.loginIdentifier.trim())
      nextErrors.loginIdentifier = 'Vui lòng nhập tên tài khoản hoặc email.'
    if (!formData.loginPassword) nextErrors.loginPassword = 'Vui lòng nhập mật khẩu.'
    return nextErrors
  }

  const validateRegistration = () => {
    const nextErrors = {}
    const emailPattern = /^[^\s@]+@[^\s@]+\.[^\s@]+$/
    const phonePattern = /^(0|\+84)[0-9]{8,10}$/

    if (!emailPattern.test(formData.email.trim())) nextErrors.email = 'Vui lòng nhập email hợp lệ.'
    if (formData.fullName.trim().length < 2) nextErrors.fullName = 'Vui lòng nhập họ và tên.'
    if (formData.phone && !phonePattern.test(formData.phone.replace(/[.\s-]/g, '')))
      nextErrors.phone = 'Số điện thoại chưa đúng định dạng.'
    if (formData.password.length < 8) nextErrors.password = 'Mật khẩu cần có ít nhất 8 ký tự.'
    if (formData.confirmPassword !== formData.password)
      nextErrors.confirmPassword = 'Mật khẩu nhập lại chưa khớp.'
    if (!formData.acceptTerms) nextErrors.acceptTerms = 'Vui lòng đồng ý với Điều khoản sử dụng.'
    return nextErrors
  }

  const handleSubmit = (event) => {
    event.preventDefault()
    const nextErrors = isRegistering ? validateRegistration() : validateLogin()

    if (Object.keys(nextErrors).length) {
      setErrors(nextErrors)
      setFeedback({ type: 'error', message: 'Vui lòng kiểm tra lại thông tin đã nhập.' })
      return
    }

    setErrors({})
    setFeedback(null)
    setIsSubmitting(true)

    window.setTimeout(() => {
      setIsSubmitting(false)
      setFeedback({
        type: 'success',
        message: isRegistering
          ? 'Đăng ký thành công (mô phỏng). Bạn có thể đăng nhập bằng tài khoản vừa tạo.'
          : 'Đăng nhập thành công (mô phỏng).',
      })
    }, 650)
  }

  const formProps = {
    formData,
    errors,
    onChange: handleChange,
    showPassword,
    onTogglePassword: () => setShowPassword((value) => !value),
  }

  return (
    <section className="auth-card" aria-label="Đăng nhập hoặc đăng ký">
      <div className="tabs" role="tablist" aria-label="Xác thực tài khoản">
        <button
          id="login-tab"
          type="button"
          role="tab"
          aria-selected={!isRegistering}
          aria-controls="login-panel"
          className={`tab ${!isRegistering ? 'active' : ''}`}
          onClick={() => changeTab('login')}
        >
          Đăng nhập
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
          Đăng ký
        </button>
      </div>

      <h3>{isRegistering ? 'Đăng ký tài khoản' : 'Chào mừng bạn quay trở lại!'}</h3>
      <p className="auth-subtitle">
        {isRegistering
          ? 'Tạo tài khoản để bắt đầu sử dụng VieTaxLegal'
          : 'Đăng nhập để tiếp tục sử dụng VieTaxLegal'}
      </p>

      <form onSubmit={handleSubmit} noValidate>
        {isRegistering ? (
          <RegisterForm
            {...formProps}
            showConfirmPassword={showConfirmPassword}
            onToggleConfirmPassword={() => setShowConfirmPassword((value) => !value)}
          />
        ) : (
          <LoginForm {...formProps} />
        )}

        {feedback && (
          <p
            className={`auth-feedback ${feedback.type}`}
            role={feedback.type === 'error' ? 'alert' : 'status'}
          >
            {feedback.message}
          </p>
        )}

        <button type="submit" className="primary-btn" disabled={isSubmitting}>
          {isSubmitting ? 'Đang xử lý...' : isRegistering ? 'Tạo tài khoản' : 'Đăng nhập'}
        </button>
        <div className="divider">
          <span>hoặc</span>
        </div>
        <button
          type="button"
          className="google-btn"
          onClick={() =>
            setFeedback({
              type: 'info',
              message: 'Đăng nhập Google sẽ được kết nối ở bước tích hợp backend.',
            })
          }
        >
          <GoogleIcon />
          {isRegistering ? 'Đăng ký với Google' : 'Tiếp tục với Google'}
        </button>
      </form>
    </section>
  )
}
