/** Shared easing and timing — tuned for Linear/Railway-style motion. */
export const EASE_OUT = [0.25, 0.1, 0.25, 1] as const

export const DURATION = {
  fast: 0.2,
  medium: 0.45,
  slow: 0.6,
} as const

export const VIEWPORT = {
  once: true,
  amount: 0.2,
  margin: '-60px 0px -40px 0px',
} as const

export const fadeUpHidden = { opacity: 0, y: 20 }
export const fadeUpVisible = { opacity: 1, y: 0 }

export const fadeUpTransition = (delay = 0) => ({
  duration: DURATION.slow,
  delay,
  ease: EASE_OUT,
})

export const staggerContainer = {
  hidden: {},
  visible: {
    transition: {
      staggerChildren: 0.09,
      delayChildren: 0.06,
    },
  },
}

export const staggerItem = {
  hidden: { opacity: 0, y: 18 },
  visible: {
    opacity: 1,
    y: 0,
    transition: { duration: DURATION.medium, ease: EASE_OUT },
  },
}

export const cardHover = {
  y: -3,
  transition: { duration: DURATION.fast, ease: EASE_OUT },
}

export const buttonTap = {
  scale: 0.98,
  transition: { duration: 0.1 },
}

export const buttonHover = {
  scale: 1.02,
  transition: { type: 'spring' as const, stiffness: 400, damping: 28 },
}

export const panelSwap = {
  initial: { opacity: 0, y: 10 },
  animate: { opacity: 1, y: 0 },
  exit: { opacity: 0, y: -8 },
  transition: { duration: DURATION.medium, ease: EASE_OUT },
}
