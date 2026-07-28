import './Process.css'
import { processIcons } from '../../data/process'
import { useI18n } from '../../i18n/useI18n'

export default function Process() {
  const { t, tList } = useI18n()
  const steps = tList('landing.process.items')

  return (
    <section className="process">
      <div className="container">
        <div className="section-header">
          <span className="eyebrow">{t('landing.process.eyebrow')}</span>
          <h2>{t('landing.process.heading')}</h2>
        </div>
        <div className="steps-grid">
          {steps.map((step, index) => (
            <article key={step.id} className="step-card">
              <span className="step-number">{index + 1}</span>
              <div className="step-icon">
                <img src={processIcons[step.id]} alt="" aria-hidden="true" />
              </div>
              <h3>{step.title}</h3>
              <p>{step.description}</p>
              {index < steps.length - 1 && (
                <div className="step-arrow" aria-hidden="true">
                  →
                </div>
              )}
            </article>
          ))}
        </div>
      </div>
    </section>
  )
}
