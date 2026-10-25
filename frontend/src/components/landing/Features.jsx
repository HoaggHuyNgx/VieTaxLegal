import aiIllustration from '../../assets/images/illustrations/ai-features-illustration.webp'
import { featureIcons } from '../../data/features'
import { useI18n } from '../../i18n/useI18n'

export default function Features() {
  const { t, tList } = useI18n()

  return (
    <section className="bg-gray-50 py-20 lte-968:py-12" id="features">
      <div className="mx-auto max-w-[1280px] px-8 lte-768:px-4">
        <div className="grid grid-cols-[1fr_1fr] items-center gap-16 lte-968:grid-cols-[1fr] lte-968:gap-8">
          <div>
            <span className="mb-4 inline-block text-[0.75rem] font-semibold tracking-[0.05em] text-blue-primary uppercase">
              {t('landing.features.eyebrow')}
            </span>
            <h2 className="mb-8 text-[2rem] leading-[1.2] font-bold text-gray-900 lte-968:text-[1.5rem]">
              {t('landing.features.heading')}
            </h2>
            <div className="flex flex-col gap-6">
              {tList('landing.features.items').map((feature) => (
                <article key={feature.id} className="flex items-start gap-4">
                  <div className="flex size-14 shrink-0 items-center justify-center rounded-xl bg-[image:var(--gradient-feature-icon)] shadow-feature-icon">
                    <img
                      className="size-8 object-contain"
                      src={featureIcons[feature.id]}
                      alt={feature.title}
                    />
                  </div>
                  <p className="m-0 pt-2 text-[0.95rem] leading-[1.6] text-gray-700">{feature.description}</p>
                </article>
              ))}
            </div>
          </div>
          <div className="aspect-[4/3] h-auto w-full overflow-hidden rounded-[20px] shadow-visual-card">
            <img
              src={aiIllustration}
              alt={t('landing.features.illustrationAlt')}
              className="block h-full w-full object-cover"
            />
          </div>
        </div>
      </div>
    </section>
  )
}
