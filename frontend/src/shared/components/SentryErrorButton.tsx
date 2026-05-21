/** Dev-only control to verify Sentry error reporting. */
export default function SentryErrorButton() {
  return (
    <button
      type="button"
      className="fixed bottom-4 right-4 rounded border border-red-300 bg-red-50 px-3 py-1.5 text-sm text-red-800 dark:border-red-800 dark:bg-red-950 dark:text-red-200"
      onClick={() => {
        throw new Error('This is your first error!')
      }}
    >
      Break the world
    </button>
  )
}
