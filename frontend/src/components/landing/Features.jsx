import './Features.css'
import aiIllustration from '../../assets/images/illustrations/ai-features-illustration.webp'
import { featureIcons } from '../../data/features'
import { useI18n } from '../../i18n/useI18n'

export default function Features() {
  const { t, tList } = useI18n()

  return (
    <section className="features" id="features">
      <div className="container">
        <div className="features-grid">
          <div className="features-content">
            <span className="eyebrow">{t('landing.features.eyebrow')}</span>
            <h2>{t('landing.features.heading')}</h2>
            <div className="feature-list">
              {tList('landing.features.items').map((feature) => (
                <article key={feature.id} className="feature-item">
                  <div className="feature-icon">
                    <img src={featureIcons[feature.id]} alt={feature.title} />
                  </div>
                  <p>{feature.description}</p>
                </article>
              ))}
            </div>
          </div>
          <div className="visual-card">
            <img
              src={aiIllustration}
              alt={t('landing.features.illustrationAlt')}
              className="ai-illustration"
            />
          </div>
        </div>
      </div>
    </section>
  )
}
