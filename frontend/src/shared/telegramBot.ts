export const TELEGRAM_BOT_USERNAME = 'hap_prod_bot'

export const TELEGRAM_BOT_WEB_URL =
  import.meta.env.VITE_TELEGRAM_BOT_URL ?? `https://telegram.me/${TELEGRAM_BOT_USERNAME}`

const TELEGRAM_BOT_DEEP_LINK = `tg://resolve?domain=${TELEGRAM_BOT_USERNAME}`

function isMobileDevice(): boolean {
  return /iPhone|iPad|iPod|Android/i.test(navigator.userAgent)
}

/** Opens the bot in the Telegram app on mobile, with web URL fallback. */
export function openTelegramBot(): void {
  if (!isMobileDevice()) {
    window.open(TELEGRAM_BOT_WEB_URL, '_blank', 'noopener,noreferrer')
    return
  }

  let fallbackTimer: ReturnType<typeof setTimeout>

  const cancelFallback = () => {
    clearTimeout(fallbackTimer)
    document.removeEventListener('visibilitychange', onVisibilityChange)
    window.removeEventListener('pagehide', cancelFallback)
  }

  const onVisibilityChange = () => {
    if (document.hidden) cancelFallback()
  }

  document.addEventListener('visibilitychange', onVisibilityChange)
  window.addEventListener('pagehide', cancelFallback)

  window.location.href = TELEGRAM_BOT_DEEP_LINK

  fallbackTimer = setTimeout(() => {
    cancelFallback()
    window.location.href = TELEGRAM_BOT_WEB_URL
  }, 1500)
}

/** @deprecated Prefer TELEGRAM_BOT_WEB_URL or openTelegramBot(). */
export function useBotUrl(): string {
  return TELEGRAM_BOT_WEB_URL
}
