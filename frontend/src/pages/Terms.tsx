import { useTranslation } from 'react-i18next'

export default function Terms() {
  const { t } = useTranslation()
  return (
    <main className="min-h-screen px-6 py-12 max-w-3xl mx-auto">
      <h1 className="text-3xl font-semibold">{t('terms.title')}</h1>
    </main>
  )
}
