import { useTranslation } from 'react-i18next'
import SentryErrorButton from '../shared/components/SentryErrorButton'

export default function Landing() {
  const { t } = useTranslation()
  const botUrl = import.meta.env.VITE_TELEGRAM_BOT_URL ?? 'https://t.me/hap_bot'

  return (
    <main className="min-h-screen flex items-center justify-center px-6">
      <div className="max-w-2xl text-center">
        <h1 className="text-5xl font-semibold tracking-tight">{t('landing.title')}</h1>
        <p className="mt-4 text-lg text-neutral-600 dark:text-neutral-300">
          {t('landing.subtitle')}
        </p>
        <a
          href={botUrl}
          className="mt-8 inline-block rounded-full bg-orange-500 px-6 py-3 text-white font-medium hover:bg-orange-600 transition"
        >
          {t('landing.cta')}
        </a>
      </div>
      {import.meta.env.DEV && import.meta.env.VITE_SENTRY_DSN ? <SentryErrorButton /> : null}
    </main>
  )
}
