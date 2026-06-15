import type { ReactNode } from 'react'
import { motion, useReducedMotion } from 'framer-motion'
import { cardHover } from '../motion/presets'

type HoverCardProps = {
  children: ReactNode
  className?: string
  glow?: boolean
}

/** Card with subtle lift on hover and optional accent glow. */
export default function HoverCard({ children, className = '', glow = false }: HoverCardProps) {
  const reduced = useReducedMotion()

  if (reduced) {
    return <div className={className}>{children}</div>
  }

  return (
    <motion.div
      className={`${className} ${glow ? 'hover-glow' : ''}`}
      whileHover={cardHover}
      transition={{ duration: 0.2 }}
    >
      {children}
    </motion.div>
  )
}
