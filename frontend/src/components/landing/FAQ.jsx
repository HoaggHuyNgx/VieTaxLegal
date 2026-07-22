import { useState } from 'react'
import './FAQ.css'
import { faqs } from '../../data/faqs'

export default function FAQ() {
  const [openIndex, setOpenIndex] = useState(null)

  return (
    <section className="faq">
      <div className="container">
        <div className="section-header">
          <span className="eyebrow">CÂU HỎI THƯỜNG GẶP</span>
        </div>
        <div className="faq-grid">
          {faqs.map((faq, index) => {
            const isOpen = openIndex === index

            return (
              <article key={faq.question} className="faq-item">
                <button
                  type="button"
                  className={`faq-question ${isOpen ? 'open' : ''}`}
                  onClick={() => setOpenIndex((current) => (current === index ? null : index))}
                  aria-expanded={isOpen}
                  aria-controls={`faq-answer-${index}`}
                >
                  {faq.question}
                  <span className="faq-icon" aria-hidden="true">
                    {isOpen ? '−' : '+'}
                  </span>
                </button>
                {isOpen && (
                  <div id={`faq-answer-${index}`} className="faq-answer">
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
