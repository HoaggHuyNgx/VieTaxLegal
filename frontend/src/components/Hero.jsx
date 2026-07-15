import './Hero.css'
import logo from '../assets/images/logo/logo.webp'
import AuthCard from './auth/AuthCard'

const benefits = [
  'Tra cứu pháp luật doanh nghiệp nhanh và chính xác.',
  'Câu trả lời có trích dẫn điều, khoản và văn bản liên quan.',
  'Phân tích hợp đồng và phát hiện điểm cần lưu ý.',
  'Hỗ trợ thuế, hóa đơn và nghĩa vụ doanh nghiệp.',
  'Giao diện đơn giản, dễ dùng cho cả doanh nghiệp và kế toán.',
  'Hoạt động 24/7, hỗ trợ ra quyết định nhanh hơn.',
]

function CheckIcon() {
  return (
    <svg width="20" height="20" viewBox="0 0 20 20" fill="currentColor" aria-hidden="true">
      <path
        fillRule="evenodd"
        d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z"
        clipRule="evenodd"
      />
    </svg>
  )
}

export default function Hero() {
  return (
    <header className="hero">
      <div className="hero-background" />

      <div className="brand-center">
        <div className="brand-logo-wrapper">
          <div className="brand-logo">
            <img src={logo} alt="VieTaxLegal" />
          </div>
          <h1 className="brand-name">VieTaxLegal</h1>
        </div>
        <p className="brand-tagline">AI pháp lý &amp; thuế cho doanh nghiệp Việt Nam</p>
        <p className="brand-description">
          Tra cứu pháp luật, phân tích hợp đồng và hỗ trợ nghiệp vụ thuế
          <br />
          với câu trả lời có căn cứ rõ ràng.
        </p>
      </div>

      <div className="container hero-content">
        <section className="hero-copy">
          <h2>VieTaxLegal</h2>
          <ul className="benefit-list">
            {benefits.map((benefit) => (
              <li key={benefit}>
                <CheckIcon />
                {benefit}
              </li>
            ))}
          </ul>
        </section>

        <AuthCard />
      </div>
    </header>
  )
}
