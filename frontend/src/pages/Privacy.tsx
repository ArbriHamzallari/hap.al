import { useTranslation } from 'react-i18next'
import { Link } from 'react-router-dom'
import LanguageToggle from '../shared/components/LanguageToggle'

export default function Privacy() {
  const { t } = useTranslation()
  const sections = [
    { title: t('privacy.collectTitle'), body: t('privacy.collectBody') },
    { title: t('privacy.useTitle'), body: t('privacy.useBody') },
    { title: t('privacy.deleteTitle'), body: t('privacy.deleteBody') },
    { title: t('privacy.lawTitle'), body: t('privacy.lawBody') },
  ]

  return (
    <main className="min-h-screen bg-neutral-50 px-6 py-10 dark:bg-neutral-950 dark:text-neutral-100">
      <div className="mx-auto max-w-2xl">
        <div className="mb-8 flex items-center justify-between">
          <Link to="/" className="text-sm text-orange-500 hover:underline">
            ← Hap
          </Link>
          <LanguageToggle />
        </div>
        <h1 className="text-3xl font-semibold">{t('privacy.title')}</h1>
        <p className="mt-2 text-sm text-neutral-500">{t('privacy.updated')}</p>
        <p className="mt-6 text-neutral-700 dark:text-neutral-300">{t('privacy.intro')}</p>
        {sections.map((s) => (
          <section key={s.title} className="mt-8">
            <h2 className="text-xl font-medium">{s.title}</h2>
            <p className="mt-2 text-neutral-700 dark:text-neutral-300">{s.body}</p>
          </section>
        ))}
      </div>
    </main>
  )
}
