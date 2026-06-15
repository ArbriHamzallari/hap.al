import { useRef, type ReactNode } from 'react'
import { motion, useInView, useReducedMotion } from 'framer-motion'
import { EASE_OUT, DURATION } from '../motion/presets'

type TelegramChatFrameProps = {
  children: ReactNode
  className?: string
  glow?: boolean
}

export function TelegramChatFrame({ children, className = '', glow = false }: TelegramChatFrameProps) {
  const reduced = useReducedMotion()

  return (
    <div className={`relative ${className}`}>
      {glow && !reduced && (
        <motion.div
          className="accent-glow-pulse"
          animate={{ opacity: [0.4, 0.7, 0.4] }}
          transition={{ duration: 5, repeat: Infinity, ease: 'easeInOut' }}
          aria-hidden
        />
      )}
      <div className="relative overflow-hidden rounded-sm border border-border bg-[#111113]">
        <div className="flex items-center gap-3 border-b border-border bg-surface px-4 py-3">
          <div className="flex h-8 w-8 items-center justify-center rounded-sm border border-border bg-card text-[10px] font-bold text-accent">
            H
          </div>
          <div>
            <p className="text-sm font-medium text-white">HAP AI</p>
            <motion.p
              className="font-mono text-[10px] uppercase tracking-wider text-accent"
              animate={reduced ? undefined : { opacity: [0.7, 1, 0.7] }}
              transition={{ duration: 3, repeat: Infinity, ease: 'easeInOut' }}
            >
              online
            </motion.p>
          </div>
        </div>
        <div className="space-y-3 bg-bg p-5">{children}</div>
      </div>
    </div>
  )
}

type BotBubbleProps = {
  children: ReactNode
  delay?: number
}

export function BotBubble({ children, delay = 0 }: BotBubbleProps) {
  const reduced = useReducedMotion()
  const ref = useRef(null)
  const inView = useInView(ref, { once: true, amount: 0.5 })

  if (reduced) {
    return (
      <div className="max-w-[92%] rounded-sm border border-border bg-card px-4 py-3.5 text-sm leading-relaxed text-white">
        {children}
      </div>
    )
  }

  return (
    <motion.div
      ref={ref}
      className="max-w-[92%] rounded-sm border border-border bg-card px-4 py-3.5 text-sm leading-relaxed text-white"
      initial={{ opacity: 0, y: 12, scale: 0.98 }}
      animate={inView ? { opacity: 1, y: 0, scale: 1 } : { opacity: 0, y: 12, scale: 0.98 }}
      transition={{ duration: DURATION.medium, delay, ease: EASE_OUT }}
    >
      {children}
    </motion.div>
  )
}

type HeroChatMockupProps = {
  sender: string
  line1: string
  line2: string
  taskLabel: string
  task: string
  deadlineLabel: string
  deadline: string
  immediate?: boolean
}

export function HeroChatMockup({
  sender,
  line1,
  line2,
  taskLabel,
  task,
  deadlineLabel,
  deadline,
  immediate = true,
}: HeroChatMockupProps) {
  const reduced = useReducedMotion()
  const ref = useRef(null)
  const inView = useInView(ref, { once: true, amount: 0.3 })
  const shouldAnimate = immediate || inView

  const lineMotion = (i: number) =>
    reduced
      ? {}
      : {
          initial: { opacity: 0, y: 8 },
          animate: shouldAnimate ? { opacity: 1, y: 0 } : { opacity: 0, y: 8 },
          transition: { duration: 0.4, delay: 0.35 + i * 0.1, ease: EASE_OUT },
        }

  return (
    <div ref={ref} className="w-full max-w-md">
      <TelegramChatFrame glow>
        <motion.p
          className="font-mono text-[10px] uppercase tracking-wider text-muted"
          {...lineMotion(0)}
        >
          {sender}
        </motion.p>
        <BotBubble delay={immediate ? 0.2 : 0}>
          <motion.p {...lineMotion(1)}>{line1}</motion.p>
          <motion.p className="mt-2.5 text-muted" {...lineMotion(2)}>
            {line2}
          </motion.p>
          <motion.div
            className="mt-4 border-t border-border pt-4"
            initial={reduced ? false : { opacity: 0 }}
            animate={shouldAnimate ? { opacity: 1 } : { opacity: 0 }}
            transition={{ duration: 0.45, delay: 0.65, ease: EASE_OUT }}
          >
            <p className="font-mono text-[10px] font-medium uppercase tracking-widest text-accent">
              {taskLabel}
            </p>
            <p className="mt-1.5 font-medium text-white">{task}</p>
            <p className="mt-3 font-mono text-xs text-muted">
              <span>{deadlineLabel}</span>{' '}
              <span className="text-white">{deadline}</span>
            </p>
          </motion.div>
        </BotBubble>
      </TelegramChatFrame>
    </div>
  )
}

type ConversationMockupProps = {
  lines: string[]
  index?: number
}

export function ConversationMockup({ lines, index = 0 }: ConversationMockupProps) {
  const reduced = useReducedMotion()
  const ref = useRef(null)
  const inView = useInView(ref, { once: true, amount: 0.25 })

  return (
    <motion.div
      ref={ref}
      initial={reduced ? false : { opacity: 0, y: 20 }}
      animate={inView ? { opacity: 1, y: 0 } : undefined}
      transition={{ duration: DURATION.slow, delay: index * 0.1, ease: EASE_OUT }}
      whileHover={reduced ? undefined : { y: -2 }}
    >
      <TelegramChatFrame>
        <BotBubble delay={index * 0.08}>
          {lines.map((line, i) => (
            <motion.p
              key={line}
              className={i > 0 ? 'mt-2.5' : undefined}
              initial={reduced ? false : { opacity: 0, y: 6 }}
              animate={inView ? { opacity: 1, y: 0 } : undefined}
              transition={{ duration: 0.35, delay: 0.2 + index * 0.1 + i * 0.08, ease: EASE_OUT }}
            >
              {line}
            </motion.p>
          ))}
        </BotBubble>
      </TelegramChatFrame>
    </motion.div>
  )
}
