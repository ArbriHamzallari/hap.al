import { useTranslation } from 'react-i18next'
import { Link } from 'react-router-dom'
import Header from '../shared/components/Header'
import Footer from '../shared/components/Footer'
import Container from '../shared/components/Container'

export default function Terms() {
  const { t } = useTranslation()
  const sections = [
    { title: t('terms.serviceTitle'), body: t('terms.serviceBody') },
    { title: t('terms.acceptableTitle'), body: t('terms.acceptableBody') },
    { title: t('terms.liabilityTitle'), body: t('terms.liabilityBody') },
    { title: t('terms.changesTitle'), body: t('terms.changesBody') },
  ]

  return (
    <div className="grid-bg min-h-screen">
      <Header />
      <main className="section-padding">
        <Container className="max-w-2xl">
          <Link
            to="/"
            className="focus-ring text-sm text-accent transition hover:text-white"
          >
            ← HAP AI
          </Link>
          <h1 className="font-heading mt-10 text-3xl font-semibold text-white">{t('terms.title')}</h1>
          <p className="mt-3 text-sm text-muted">{t('terms.updated')}</p>
          <p className="mt-8 leading-relaxed text-muted">{t('terms.intro')}</p>
          {sections.map((s) => (
            <section key={s.title} className="mt-12">
              <h2 className="font-heading text-xl font-semibold text-white">{s.title}</h2>
              <p className="mt-3 leading-relaxed text-muted">{s.body}</p>
            </section>
          ))}
        </Container>
      </main>
      <Footer />
    </div>
  )
}
