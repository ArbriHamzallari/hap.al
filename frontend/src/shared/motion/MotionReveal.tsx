import type { ReactNode } from 'react'
import { motion, useReducedMotion } from 'framer-motion'
import { fadeUpHidden, fadeUpTransition, fadeUpVisible, VIEWPORT } from './presets'

type MotionRevealProps = {
  children: ReactNode
  className?: string
  delay?: number
  /** Use for above-the-fold content that should animate on mount. */
  immediate?: boolean
}

/** Scroll-triggered fade-up reveal. Respects prefers-reduced-motion. */
export default function MotionReveal({
  children,
  className = '',
  delay = 0,
  immediate = false,
}: MotionRevealProps) {
  const reduced = useReducedMotion()

  if (reduced) {
    return <div className={className}>{children}</div>
  }

  if (immediate) {
    return (
      <motion.div
        className={className}
        initial={fadeUpHidden}
        animate={fadeUpVisible}
        transition={fadeUpTransition(delay)}
      >
        {children}
      </motion.div>
    )
  }

  return (
    <motion.div
      className={className}
      initial={fadeUpHidden}
      whileInView={fadeUpVisible}
      viewport={VIEWPORT}
      transition={fadeUpTransition(delay)}
    >
      {children}
    </motion.div>
  )
}

type MotionStaggerProps = {
  children: ReactNode
  className?: string
}

export function MotionStagger({ children, className = '' }: MotionStaggerProps) {
  const reduced = useReducedMotion()

  if (reduced) {
    return <div className={className}>{children}</div>
  }

  return (
    <motion.div
      className={className}
      initial="hidden"
      whileInView="visible"
      viewport={VIEWPORT}
      variants={{
        hidden: {},
        visible: {
          transition: { staggerChildren: 0.09, delayChildren: 0.06 },
        },
      }}
    >
      {children}
    </motion.div>
  )
}

export function MotionStaggerItem({
  children,
  className = '',
}: {
  children: ReactNode
  className?: string
}) {
  const reduced = useReducedMotion()

  if (reduced) {
    return <div className={className}>{children}</div>
  }

  return (
    <motion.div
      className={className}
      variants={{
        hidden: { opacity: 0, y: 18 },
        visible: {
          opacity: 1,
          y: 0,
          transition: { duration: 0.45, ease: [0.25, 0.1, 0.25, 1] },
        },
      }}
    >
      {children}
    </motion.div>
  )
}
