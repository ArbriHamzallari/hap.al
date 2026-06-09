import { useTranslation } from 'react-i18next'
import { Link } from 'react-router-dom'
import LanguageToggle from '../shared/components/LanguageToggle'
import SentryErrorButton from '../shared/components/SentryErrorButton'

export default function Landing() {
  const { t } = useTranslation()
  const botUrl = import.meta.env.VITE_TELEGRAM_BOT_URL ?? 'https://t.me/hap_bot'

  const steps = [
    { title: t('landing.step1Title'), body: t('landing.step1Body') },
    { title: t('landing.step2Title'), body: t('landing.step2Body') },
    { title: t('landing.step3Title'), body: t('landing.step3Body') },
  ]

  return (
    <main className="min-h-screen bg-neutral-50 text-neutral-900 dark:bg-neutral-950 dark:text-neutral-100">
      <header className="flex justify-end px-6 py-4">
        <LanguageToggle />
      </header>

      <section className="mx-auto max-w-3xl px-6 pb-16 pt-8 text-center">
        <h1 className="text-4xl font-semibold tracking-tight sm:text-5xl">{t('landing.title')}</h1>
        <p className="mt-4 text-lg text-neutral-600 dark:text-neutral-300">{t('landing.subtitle')}</p>
        <a
          href={botUrl}
          className="mt-8 inline-block rounded-full bg-orange-500 px-8 py-3 font-medium text-white transition hover:bg-orange-600"
        >
          {t('landing.cta')}
        </a>
        <ul className="mt-10 flex flex-wrap justify-center gap-6 text-sm text-neutral-500 dark:text-neutral-400">
          <li>{t('landing.trustFree')}</li>
          <li>{t('landing.trustEncrypted')}</li>
          <li>{t('landing.trustNoSignup')}</li>
        </ul>
      </section>

      <section className="mx-auto max-w-4xl px-6 pb-20">
        <h2 className="text-center text-2xl font-semibold">{t('landing.howTitle')}</h2>
        <ol className="mt-10 grid gap-8 sm:grid-cols-3">
          {steps.map((step, i) => (
            <li
              key={step.title}
              className="rounded-2xl border border-neutral-200 bg-white p-6 dark:border-neutral-800 dark:bg-neutral-900"
            >
              <span className="text-sm font-medium text-orange-500">0{i + 1}</span>
              <h3 className="mt-2 text-lg font-medium">{step.title}</h3>
              <p className="mt-2 text-sm text-neutral-600 dark:text-neutral-400">{step.body}</p>
            </li>
          ))}
        </ol>
      </section>

      <footer className="border-t border-neutral-200 px-6 py-8 text-center text-sm text-neutral-500 dark:border-neutral-800">
        <Link to="/privacy" className="hover:text-orange-500">
          {t('privacy.title')}
        </Link>
        <span className="mx-3">·</span>
        <Link to="/terms" className="hover:text-orange-500">
          {t('terms.title')}
        </Link>
      </footer>

      {import.meta.env.DEV && import.meta.env.VITE_SENTRY_DSN ? <SentryErrorButton /> : null}
    </main>
  )
}
