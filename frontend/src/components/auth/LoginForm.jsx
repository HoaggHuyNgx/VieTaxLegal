import { EyeIcon, FieldError } from './AuthIcons'

export default function LoginForm({
  formData,
  errors,
  onChange,
  showPassword,
  onTogglePassword,
  onForgotPassword,
}) {
  return (
    <div id="login-panel" role="tabpanel" aria-labelledby="login-tab">
      <div className="form-group">
        <label htmlFor="login-identifier">Tên tài khoản hoặc email</label>
        <input
          id="login-identifier"
          name="loginIdentifier"
          type="text"
          autoComplete="username"
          placeholder="Nhập tên tài khoản hoặc email"
          value={formData.loginIdentifier}
          onChange={onChange}
          aria-invalid={Boolean(errors.loginIdentifier)}
          aria-describedby={errors.loginIdentifier ? 'login-identifier-error' : undefined}
        />
        <FieldError error={errors.loginIdentifier} id="login-identifier-error" />
      </div>
      <div className="form-group">
        <label htmlFor="login-password">Mật khẩu</label>
        <div className="password-input">
          <input
            id="login-password"
            name="loginPassword"
            type={showPassword ? 'text' : 'password'}
            autoComplete="current-password"
            placeholder="Nhập mật khẩu"
            value={formData.loginPassword}
            onChange={onChange}
            aria-invalid={Boolean(errors.loginPassword)}
            aria-describedby={errors.loginPassword ? 'login-password-error' : undefined}
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
        <FieldError error={errors.loginPassword} id="login-password-error" />
      </div>
      <div className="form-row">
        <label className="checkbox-label">
          <input type="checkbox" name="rememberMe" checked={formData.rememberMe} onChange={onChange} />
          Ghi nhớ đăng nhập
        </label>
        <button type="button" className="forgot-link" onClick={onForgotPassword}>
          Quên mật khẩu?
        </button>
      </div>
    </div>
  )
}
