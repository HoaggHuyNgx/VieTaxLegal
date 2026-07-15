import './Footer.css'
import logo from '../assets/images/logo/logo.webp'

export default function Footer() {
  return (
    <footer className="footer">
      <div className="container">
        <div className="footer-main">
          <section className="footer-brand" aria-label="VieTaxLegal">
            <div className="footer-brand-row">
              <div className="footer-logo">
                <img src={logo} alt="VieTaxLegal" />
              </div>
              <h3>VieTaxLegal</h3>
            </div>
            <p>
              Trợ lý pháp lý và thuế thông minh
              <br />
              cho doanh nghiệp Việt Nam
            </p>
          </section>

          <div className="footer-divider" aria-hidden="true" />

          <div className="footer-details">
            <nav className="footer-nav" aria-label="Điều hướng chân trang">
              <a href="#features">Sản phẩm</a>
              <a href="#features">Tính năng</a>
              <a href="#pricing">Bảng giá</a>
              <a href="#contact">Liên hệ</a>
              <a href="#privacy">Chính sách bảo mật</a>
            </nav>

            <a className="footer-contact" href="mailto:hello@vietaxlegal.vn">
              <svg width="18" height="18" viewBox="0 0 24 24" fill="none" aria-hidden="true">
                <rect x="3" y="5" width="18" height="14" rx="2" stroke="currentColor" strokeWidth="1.8" />
                <path
                  d="M4 7L12 13L20 7"
                  stroke="currentColor"
                  strokeWidth="1.8"
                  strokeLinecap="round"
                  strokeLinejoin="round"
                />
              </svg>
              <span>Email: hello@vietaxlegal.vn</span>
            </a>
          </div>
        </div>

        <a href="#top" className="back-to-top" aria-label="Lên đầu trang">
          ↑
        </a>
      </div>
    </footer>
  )
}
