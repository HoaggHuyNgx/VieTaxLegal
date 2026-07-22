import './Hero.css'
import logo from '../assets/images/logo/logo.webp'
import AuthCard from './auth/AuthCard'

const benefits = [
  'Đặt câu hỏi pháp luật bằng tiếng Việt.',
  'Nhận câu trả lời trực tiếp trong thời gian thực.',
  'Lưu và tìm lại lịch sử theo từng tài khoản.',
  'Dữ liệu hội thoại chỉ được truy cập qua backend bảo vệ.',
  'Giao diện đơn giản, phù hợp để tra cứu ban đầu.',
  'Luôn nhắc kiểm tra hiệu lực văn bản trước khi áp dụng.',
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
        <p className="brand-tagline">Trợ lý tra cứu pháp luật cho doanh nghiệp Việt Nam</p>
        <p className="brand-description">
          Đặt câu hỏi, nhận phản hồi trực tiếp và lưu lại lịch sử
          <br />
          trong một không gian riêng cho tài khoản của bạn.
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
