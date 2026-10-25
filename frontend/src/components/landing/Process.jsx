import { processIcons } from '../../data/process'
import { useI18n } from '../../i18n/useI18n'

export default function Process() {
  const { t, tList } = useI18n()
  const steps = tList('landing.process.items')

  return (
    <section className="bg-white pt-20 pb-6 lte-640:py-12">
      <div className="mx-auto max-w-[1280px] px-8 lte-768:px-4">
        <div className="mb-12 text-center">
          <span className="mb-3 inline-block text-[0.75rem] font-semibold tracking-[0.05em] text-blue-primary uppercase">
            {t('landing.process.eyebrow')}
          </span>
          <h2 className="text-[2rem] font-bold text-gray-900 lte-640:text-[1.5rem]">
            {t('landing.process.heading')}
          </h2>
        </div>
        <div className="relative grid grid-cols-[repeat(4,1fr)] gap-8 lte-1024:grid-cols-[repeat(2,1fr)] lte-640:grid-cols-[1fr]">
          {steps.map((step, index) => (
            <article
              key={step.id}
              className="relative rounded-2xl border border-gray-200 bg-white px-6 py-8 text-center transition-all duration-300 ease-[ease] hover:border-blue-primary hover:shadow-step-hover hover:[transform:translateY(-4px)] lte-640:px-4 lte-640:py-6"
            >
              <span className="absolute top-4 left-4 flex size-8 items-center justify-center rounded-[50%] bg-blue-primary text-[0.875rem] font-semibold text-white">
                {index + 1}
              </span>
              <div className="mx-auto mt-4 mb-5 flex size-[4.25rem] items-center justify-center rounded-[50%] bg-[image:var(--gradient-step-icon)] shadow-step-icon">
                <img
                  className="size-[2.85rem] object-contain"
                  src={processIcons[step.id]}
                  alt=""
                  aria-hidden="true"
                />
              </div>
              <h3 className="mb-3 text-[1.125rem] font-semibold text-gray-900">{step.title}</h3>
              <p className="m-0 text-[0.875rem] leading-[1.6] text-gray-700">{step.description}</p>
              {index < steps.length - 1 && (
                // Hidden on every card at the 2-column breakpoint where the arrow would point
                // off the row (even cards end a row), and everywhere once the grid is 1 column.
                <div
                  className={`absolute top-1/2 -right-8 z-1 [transform:translateY(-50%)] text-[1.5rem] text-gray-300 lte-640:hidden ${index % 2 === 1 ? 'lte-1024:hidden' : ''}`}
                  aria-hidden="true"
                >
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
