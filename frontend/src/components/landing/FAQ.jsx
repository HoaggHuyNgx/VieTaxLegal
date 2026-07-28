import { useState } from 'react'
import './FAQ.css'
import { useI18n } from '../../i18n/useI18n'

export default function FAQ() {
  const { t, tList } = useI18n()
  // Keyed by id, not by index: switching locale must not reopen a different item.
  const [openId, setOpenId] = useState(null)

  return (
    <section className="faq">
      <div className="container">
        <div className="section-header">
          <span className="eyebrow">{t('landing.faq.eyebrow')}</span>
        </div>
        <div className="faq-grid">
          {tList('landing.faq.items').map((faq) => {
            const isOpen = openId === faq.id

            return (
              <article key={faq.id} className="faq-item">
                <button
                  type="button"
                  className={`faq-question ${isOpen ? 'open' : ''}`}
                  onClick={() => setOpenId((current) => (current === faq.id ? null : faq.id))}
                  aria-expanded={isOpen}
                  aria-controls={`faq-answer-${faq.id}`}
                >
                  {faq.question}
                  <span className="faq-icon" aria-hidden="true">
                    {isOpen ? '−' : '+'}
                  </span>
                </button>
                {isOpen && (
                  <div id={`faq-answer-${faq.id}`} className="faq-answer">
                    <p>{faq.answer}</p>
                  </div>
                )}
              </article>
            )
          })}
        </div>
      </div>
    </section>
  )
}
