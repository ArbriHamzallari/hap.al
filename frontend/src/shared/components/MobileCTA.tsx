import { motion, useReducedMotion } from 'framer-motion'
import { useTranslation } from 'react-i18next'
import Button from './Button'
import { useBotUrl } from '../hooks/useBotUrl'

export default function MobileCTA() {
  const { t } = useTranslation()
  const botUrl = useBotUrl()
  const reduced = useReducedMotion()

  return (
    <motion.div
      className="fixed bottom-0 left-0 right-0 z-50 border-t border-border bg-bg/95 p-4 backdrop-blur-sm sm:hidden"
      initial={reduced ? false : { y: 80, opacity: 0 }}
      animate={{ y: 0, opacity: 1 }}
      transition={{ duration: 0.45, delay: 0.8, ease: [0.25, 0.1, 0.25, 1] }}
    >
      <Button href={botUrl} className="w-full">
        {t('landing.ctaPrimary')}
      </Button>
    </motion.div>
  )
}
