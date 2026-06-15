export function useBotUrl(): string {
  return import.meta.env.VITE_TELEGRAM_BOT_URL ?? 'https://t.me/hap_prod_bot'
}
