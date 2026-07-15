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
  return (
    <div id="register-panel" className="register-fields" role="tabpanel" aria-labelledby="register-tab">
      <div className="form-group">
        <label htmlFor="register-email">
          Email <span className="required-mark">*</span>
        </label>
        <input
          id="register-email"
          name="email"
          type="email"
          autoComplete="email"
          placeholder="Nhập email của bạn"
          value={formData.email}
          onChange={onChange}
          aria-invalid={Boolean(errors.email)}
          aria-describedby={errors.email ? 'register-email-error' : undefined}
        />
        <FieldError error={errors.email} id="register-email-error" />
      </div>
      <div className="form-group">
        <label htmlFor="full-name">
          Họ và tên <span className="required-mark">*</span>
        </label>
        <input
          id="full-name"
          name="fullName"
          type="text"
          autoComplete="name"
          placeholder="Nhập họ và tên"
          value={formData.fullName}
          onChange={onChange}
          aria-invalid={Boolean(errors.fullName)}
          aria-describedby={errors.fullName ? 'full-name-error' : undefined}
        />
        <FieldError error={errors.fullName} id="full-name-error" />
      </div>
      <div className="form-group">
        <label htmlFor="phone">
          Số điện thoại <span className="optional-mark">(không bắt buộc)</span>
        </label>
        <input
          id="phone"
          name="phone"
          type="tel"
          inputMode="tel"
          autoComplete="tel"
          placeholder="Ví dụ: 0901234567"
          value={formData.phone}
          onChange={onChange}
          aria-invalid={Boolean(errors.phone)}
          aria-describedby={errors.phone ? 'phone-error' : undefined}
        />
        <FieldError error={errors.phone} id="phone-error" />
      </div>
      <div className="form-group">
        <label htmlFor="register-password">
          Mật khẩu <span className="required-mark">*</span>
        </label>
        <div className="password-input">
          <input
            id="register-password"
            name="password"
            type={showPassword ? 'text' : 'password'}
            autoComplete="new-password"
            placeholder="Tối thiểu 8 ký tự"
            value={formData.password}
            onChange={onChange}
            aria-invalid={Boolean(errors.password)}
            aria-describedby={errors.password ? 'register-password-error' : undefined}
          />
          <button
            type="button"
            className="toggle-password"
            onClick={onTogglePassword}
            aria-label={showPassword ? 'Ẩn mật khẩu' : 'Hiện mật khẩu'}
          >
            <EyeIcon hidden={showPassword} />
          </button>
        </div>
        <FieldError error={errors.password} id="register-password-error" />
      </div>
      <div className="form-group">
        <label htmlFor="confirm-password">
          Nhập lại mật khẩu <span className="required-mark">*</span>
        </label>
        <div className="password-input">
          <input
            id="confirm-password"
            name="confirmPassword"
            type={showConfirmPassword ? 'text' : 'password'}
            autoComplete="new-password"
            placeholder="Nhập lại mật khẩu"
            value={formData.confirmPassword}
            onChange={onChange}
            aria-invalid={Boolean(errors.confirmPassword)}
            aria-describedby={errors.confirmPassword ? 'confirm-password-error' : undefined}
          />
          <button
            type="button"
            className="toggle-password"
            onClick={onToggleConfirmPassword}
            aria-label={showConfirmPassword ? 'Ẩn mật khẩu nhập lại' : 'Hiện mật khẩu nhập lại'}
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
          Tôi đồng ý với <a href="#terms">Điều khoản sử dụng</a> và <a href="#privacy">Chính sách bảo mật</a>.
        </span>
      </label>
      <FieldError error={errors.acceptTerms} id="accept-terms-error" />
    </div>
  )
}
