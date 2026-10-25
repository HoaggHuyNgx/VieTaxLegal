import { useState } from 'react'
import { useI18n } from '../../i18n/useI18n'

// `faq-question` carries no styles: the visual-regression helper clicks it by name.
const QUESTION_BASE =
  'faq-question flex w-full cursor-pointer items-center justify-between gap-4 border-none px-4 py-3 text-left text-[0.95rem] font-medium transition-all duration-200 ease-[ease] lte-768:p-4 lte-768:text-[0.875rem]'
const QUESTION_OPEN = 'bg-gray-50 text-blue-primary'
const QUESTION_CLOSED = 'bg-white text-gray-900 hover:bg-gray-50'

export default function FAQ() {
  const { t, tList } = useI18n()
  // Keyed by id, not by index: switching locale must not reopen a different item.
  const [openId, setOpenId] = useState(null)

  return (
    <section className="bg-white pt-6 pb-4 lte-768:py-6">
      <div className="mx-auto max-w-[1280px] px-8 lte-768:px-4">
        <div className="mb-3 text-center">
          <span className="mb-3 inline-block text-[1rem] font-bold tracking-[0.05em] text-blue-primary uppercase">
            {t('landing.faq.eyebrow')}
          </span>
        </div>
        <div className="mx-auto grid max-w-none grid-cols-[repeat(2,1fr)] gap-x-3 gap-y-2 lte-768:grid-cols-[1fr]">
          {tList('landing.faq.items').map((faq) => {
            const isOpen = openId === faq.id

            return (
              <article
                key={faq.id}
                className="overflow-hidden rounded-lg border border-gray-200 transition-all duration-300 ease-[ease] hover:border-blue-primary hover:shadow-faq-item"
              >
                <button
                  type="button"
                  className={`${QUESTION_BASE} ${isOpen ? QUESTION_OPEN : QUESTION_CLOSED}`}
                  onClick={() => setOpenId((current) => (current === faq.id ? null : faq.id))}
                  aria-expanded={isOpen}
                  aria-controls={`faq-answer-${faq.id}`}
                >
                  {faq.question}
                  <span
                    className="flex size-6 shrink-0 items-center justify-center text-[1.25rem] leading-none font-light text-blue-primary"
                    aria-hidden="true"
                  >
                    {isOpen ? '−' : '+'}
                  </span>
                </button>
                {isOpen && (
                  <div id={`faq-answer-${faq.id}`} className="animate-[slideDown_0.3s_ease] px-4 pb-4">
                    <p className="m-0 text-[0.875rem] leading-[1.6] text-gray-700">{faq.answer}</p>
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
