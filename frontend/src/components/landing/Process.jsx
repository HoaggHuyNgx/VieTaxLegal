import './Process.css'
import { processSteps } from '../../data/process'

export default function Process() {
  return (
    <section className="process">
      <div className="container">
        <div className="section-header">
          <span className="eyebrow">CÁCH VIETAXLEGAL HỖ TRỢ BẠN</span>
          <h2>Quy trình hoạt động</h2>
        </div>
        <div className="steps-grid">
          {processSteps.map((step, index) => (
            <article key={step.number} className="step-card">
              <span className="step-number">{step.number}</span>
              <div className="step-icon">
                <img src={step.icon} alt="" aria-hidden="true" />
              </div>
              <h3>{step.title}</h3>
              <p>{step.description}</p>
              {index < processSteps.length - 1 && (
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
