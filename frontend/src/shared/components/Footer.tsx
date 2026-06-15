import { Link } from 'react-router-dom'
import { useTranslation } from 'react-i18next'
import Container from './Container'
import { openTelegramBot, useBotUrl } from '../telegramBot'

export default function Footer() {
  const { t } = useTranslation()
  const botUrl = useBotUrl()

  return (
    <footer className="border-t border-white/8 py-14">
      <Container>
        <div className="flex flex-col items-center gap-8 text-center sm:flex-row sm:justify-between sm:text-left">
          <div className="flex items-center gap-3">
            <span className="font-heading flex h-8 w-8 items-center justify-center rounded-full bg-accent text-xs font-black text-bg">
              H
            </span>
            <div>
              <p className="font-heading text-sm font-semibold text-white">HAP AI</p>
              <p className="text-xs text-muted">{t('landing.footer.tagline')}</p>
            </div>
          </div>

          <nav className="flex flex-wrap items-center justify-center gap-x-6 gap-y-2 text-sm text-muted">
            <a
              href={botUrl}
              onClick={(event) => {
                event.preventDefault()
                openTelegramBot()
              }}
              className="focus-ring transition-colors hover:text-white"
            >
              {t('nav.launch')}
            </a>
            <Link to="/privacy" className="focus-ring transition-colors hover:text-white">
              {t('privacy.title')}
            </Link>
            <Link to="/terms" className="focus-ring transition-colors hover:text-white">
              {t('terms.title')}
            </Link>
          </nav>
        </div>

        <div className="mt-10 border-t border-white/8 pt-6 text-center">
          <p className="font-mono text-xs tracking-tight text-muted/70">
            © 2026 HAP AI. Built by Arbri Hamzallari.
          </p>
        </div>
      </Container>
    </footer>
  )
}
