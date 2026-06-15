import i18n from 'i18next'
import { initReactI18next } from 'react-i18next'
import en from './en.json'
import sq from './sq.json'

function detectLanguage(): 'en' | 'sq' {
  const stored = localStorage.getItem('hap-lang')
  if (stored === 'en' || stored === 'sq') return stored
  if (typeof navigator !== 'undefined' && navigator.language?.startsWith('sq')) return 'sq'
  return 'en'
}

const initialLang = typeof window !== 'undefined' ? detectLanguage() : 'en'

if (typeof document !== 'undefined') {
  document.documentElement.lang = initialLang
}

void i18n.use(initReactI18next).init({
  resources: {
    en: { translation: en },
    sq: { translation: sq },
  },
  lng: initialLang,
  fallbackLng: 'en',
  interpolation: { escapeValue: false },
})

export default i18n
