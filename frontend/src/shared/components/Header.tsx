import { motion, useReducedMotion } from 'framer-motion'
import { useTranslation } from 'react-i18next'
import { Link } from 'react-router-dom'
import LanguageToggle from './LanguageToggle'
import Button from './Button'
import { useBotUrl } from '../hooks/useBotUrl'
import { EASE_OUT } from '../motion/presets'

export default function Header() {
  const { t } = useTranslation()
  const botUrl = useBotUrl()
  const reduced = useReducedMotion()

  return (
    <motion.header
      className="sticky top-3 z-50 px-3"
      initial={reduced ? false : { opacity: 0, y: -8 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.45, ease: EASE_OUT }}
    >
      <div className="mx-auto flex max-w-6xl items-center justify-between gap-3 rounded-full border border-white/10 bg-bg/75 px-4 py-2.5 shadow-[0_18px_70px_rgba(0,0,0,0.35)] backdrop-blur-xl sm:px-5 sm:py-3 lg:px-7">
        <Link
          to="/"
          className="focus-ring font-heading group flex shrink-0 items-center gap-2.5 whitespace-nowrap text-sm font-semibold tracking-tight text-white"
        >
          <motion.span
            className="flex h-7 w-7 items-center justify-center rounded-full border border-accent/25 bg-accent text-xs font-black text-bg"
            whileHover={reduced ? undefined : { scale: 1.05 }}
            whileTap={reduced ? undefined : { scale: 0.95 }}
            transition={{ type: 'spring', stiffness: 400, damping: 25 }}
          >
            H
          </motion.span>
          HAP AI
        </Link>
        <div className="flex items-center gap-3 sm:gap-4">
          <LanguageToggle />
          <span className="hidden sm:inline-flex">
            <Button href={botUrl} telegramBot>
              {t('nav.launch')}
            </Button>
          </span>
        </div>
      </div>
    </motion.header>
  )
}
