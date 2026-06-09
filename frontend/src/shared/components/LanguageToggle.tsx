import { useTranslation } from 'react-i18next'

export default function LanguageToggle() {
  const { i18n, t } = useTranslation()
  const current = i18n.language.startsWith('sq') ? 'sq' : 'en'

  return (
    <div className="inline-flex rounded-full border border-neutral-300 p-0.5 text-sm dark:border-neutral-600">
      {(['en', 'sq'] as const).map((code) => (
        <button
          key={code}
          type="button"
          onClick={() => void i18n.changeLanguage(code)}
          className={`rounded-full px-3 py-1 transition ${
            current === code
              ? 'bg-orange-500 text-white'
              : 'text-neutral-600 hover:text-neutral-900 dark:text-neutral-400 dark:hover:text-neutral-100'
          }`}
        >
          {t(`lang.${code}`)}
        </button>
      ))}
    </div>
  )
}
