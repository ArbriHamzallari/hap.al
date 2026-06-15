import type { MouseEvent, ReactNode } from 'react'
import { motion, useReducedMotion } from 'framer-motion'
import { buttonHover, buttonTap } from '../motion/presets'
import { openTelegramBot } from '../telegramBot'

type ButtonVariant = 'primary' | 'secondary' | 'ghost'

type ButtonProps = {
  children: ReactNode
  variant?: ButtonVariant
  href?: string
  /** Try tg:// on mobile, then fall back to the href web URL. */
  telegramBot?: boolean
  onClick?: () => void
  className?: string
}

const variants: Record<ButtonVariant, string> = {
  primary:
    'bg-accent text-bg hover:bg-accent-dim focus-visible:outline-accent/50 btn-glow',
  secondary:
    'border border-border bg-surface text-white hover:border-border-strong hover:bg-card focus-visible:outline-accent/50',
  ghost: 'text-muted hover:text-white focus-visible:outline-accent/50',
}

export default function Button({
  children,
  variant = 'primary',
  href,
  telegramBot = false,
  onClick,
  className = '',
}: ButtonProps) {
  const reduced = useReducedMotion()
  const base =
    'focus-ring relative inline-flex items-center justify-center rounded-sm px-5 py-2.5 text-sm font-medium transition-colors duration-150'
  const classes = `${base} ${variants[variant]} ${className}`

  const motionProps = reduced
    ? {}
    : {
        whileHover: buttonHover,
        whileTap: buttonTap,
      }

  if (href) {
    const handleClick = (event: MouseEvent<HTMLAnchorElement>) => {
      if (telegramBot) {
        event.preventDefault()
        openTelegramBot()
      }
      onClick?.()
    }

    return (
      <motion.a
        href={href}
        target={telegramBot ? undefined : '_blank'}
        rel={telegramBot ? undefined : 'noopener noreferrer'}
        onClick={telegramBot || onClick ? handleClick : undefined}
        className={classes}
        {...motionProps}
      >
        {children}
      </motion.a>
    )
  }

  return (
    <motion.button type="button" onClick={onClick} className={classes} {...motionProps}>
      {children}
    </motion.button>
  )
}
