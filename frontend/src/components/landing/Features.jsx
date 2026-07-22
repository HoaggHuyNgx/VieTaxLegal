import './Features.css'
import aiIllustration from '../../assets/images/illustrations/ai-features-illustration.webp'
import { featureItems } from '../../data/features'

export default function Features() {
  return (
    <section className="features" id="features">
      <div className="container">
        <div className="features-grid">
          <div className="features-content">
            <span className="eyebrow">TẠI SAO NÊN CHỌN VIETAXLEGAL</span>
            <h2>Đặc điểm nổi bật của VieTaxLegal</h2>
            <div className="feature-list">
              {featureItems.map((feature) => (
                <article key={feature.title} className="feature-item">
                  <div className="feature-icon">
                    <img src={feature.icon} alt={feature.title} />
                  </div>
                  <p>{feature.description}</p>
                </article>
              ))}
            </div>
          </div>
          <div className="visual-card">
            <img src={aiIllustration} alt="Trợ lý tra cứu pháp luật" className="ai-illustration" />
          </div>
        </div>
      </div>
    </section>
  )
}
