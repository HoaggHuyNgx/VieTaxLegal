import { useI18n } from '../../i18n/useI18n'

export default function ErrorFallback() {
  const { t } = useI18n()
  return (
    <main className="grid min-h-dvh place-content-center justify-items-center gap-4 bg-chat-canvas p-6 text-center text-chat-ink">
      <p className="m-0 max-w-[420px] text-[14px]" role="alert">
        {t('common.errorBoundary.message')}
      </p>
      <button
        type="button"
        className="rounded-chat border border-chat-border bg-chat-surface px-4 py-2 text-[13px]"
        onClick={() => window.location.reload()}
      >
        {t('common.errorBoundary.reload')}
      </button>
    </main>
  )
}
