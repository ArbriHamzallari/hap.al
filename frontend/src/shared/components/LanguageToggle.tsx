import { useEffect } from 'react'
import { motion, useReducedMotion } from 'framer-motion'
import { useTranslation } from 'react-i18next'

export default function LanguageToggle() {
  const { i18n, t } = useTranslation()
  const current = i18n.language.startsWith('sq') ? 'sq' : 'en'
  const reduced = useReducedMotion()

  useEffect(() => {
    document.documentElement.lang = current
  }, [current])

  const changeLanguage = (code: 'en' | 'sq') => {
    void i18n.changeLanguage(code)
    localStorage.setItem('hap-lang', code)
  }

  return (
    <div
      role="group"
      aria-label="Language"
      className="relative inline-flex rounded-sm border border-border bg-surface p-0.5 text-xs"
    >
      {(['en', 'sq'] as const).map((code) => (
        <button
          key={code}
          type="button"
          onClick={() => changeLanguage(code)}
          aria-pressed={current === code}
          className={`focus-ring relative z-10 rounded-sm px-2.5 py-1 font-medium transition-colors duration-150 ${
            current === code ? 'text-white' : 'text-muted hover:text-white'
          }`}
        >
          {current === code && !reduced && (
            <motion.span
              layoutId="lang-indicator"
              className="absolute inset-0 rounded-sm bg-card"
              style={{ zIndex: -1 }}
              transition={{ type: 'spring', stiffness: 380, damping: 30 }}
            />
          )}
          {current === code && reduced && (
            <span className="absolute inset-0 rounded-sm bg-card" style={{ zIndex: -1 }} />
          )}
          {t(`lang.${code}`)}
        </button>
      ))}
    </div>
  )
}
