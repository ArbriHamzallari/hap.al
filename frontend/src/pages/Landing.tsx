import { useRef } from 'react'
import {
  motion,
  useReducedMotion,
  useScroll,
  useTransform,
  type MotionValue,
} from 'framer-motion'
import { useTranslation } from 'react-i18next'
import SentryErrorButton from '../shared/components/SentryErrorButton'
import Header from '../shared/components/Header'
import Footer from '../shared/components/Footer'
import Button from '../shared/components/Button'
import Container from '../shared/components/Container'
import MobileCTA from '../shared/components/MobileCTA'
import { useBotUrl } from '../shared/hooks/useBotUrl'
import MotionReveal from '../shared/motion/MotionReveal'
import { DURATION, EASE_OUT } from '../shared/motion/presets'

const CAPABILITY_KEYS = ['challenge', 'plans', 'tasks', 'accountability'] as const
const JOURNEY_KEYS = ['idea', 'validation', 'customers', 'mvp', 'launch'] as const
const CHAPTER_KEYS = ['challenge', 'plan', 'task', 'followup'] as const

const clamp01 = (value: number) => Math.min(1, Math.max(0, value))

function getStringList(value: unknown): string[] {
  return Array.isArray(value) ? value.filter((item): item is string => typeof item === 'string') : []
}

type ChatLine = {
  role: 'user' | 'hap' | 'system'
  text: string
  meta?: string
}

type PhoneScreen = {
  label: string
  title: string
  messages: ChatLine[]
  footer?: string
}

/* ---------- Robust i18n fallbacks (a missing/late object must never blank the page) ---------- */

const FALLBACK_HERO_SCREEN: PhoneScreen = {
  label: 'AI cofounder',
  title: 'Today',
  messages: [
    { role: 'hap', text: 'Your target audience is too broad.', meta: '09:41' },
    { role: 'hap', text: 'Pick one specific niche before tomorrow.', meta: '09:41' },
    { role: 'system', text: "Today's task" },
    { role: 'hap', text: 'Interview 5 potential customers.', meta: 'Deadline: Friday' },
    { role: 'user', text: 'Okay, working on it.', meta: '09:42' },
  ],
  footer: 'A real conversation, every day.',
}

const FALLBACK_PHONE_SCREENS: PhoneScreen[] = [FALLBACK_HERO_SCREEN]

function isPhoneScreen(value: unknown): value is PhoneScreen {
  return (
    typeof value === 'object' &&
    value !== null &&
    'messages' in value &&
    Array.isArray((value as PhoneScreen).messages)
  )
}

function getPhoneScreen(value: unknown, fallback: PhoneScreen): PhoneScreen {
  return isPhoneScreen(value) ? value : fallback
}

function getPhoneScreens(value: unknown): PhoneScreen[] {
  return Array.isArray(value) && value.length > 0 && value.every(isPhoneScreen)
    ? value
    : FALLBACK_PHONE_SCREENS
}

/* ---------- Phone primitives ---------- */

function TickIcon() {
  return (
    <svg viewBox="0 0 16 11" className="ml-1 inline h-2.5 w-3.5 align-middle" fill="none" aria-hidden>
      <path d="M1 6l3 3 6-7" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" strokeLinejoin="round" />
      <path d="M6 9l6-7" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" strokeLinejoin="round" />
    </svg>
  )
}

type RevealMode = 'mount' | 'inview' | 'none'

function ChatBubble({ line, index, reveal }: { line: ChatLine; index: number; reveal: RevealMode }) {
  const reduced = useReducedMotion()
  const isUser = line.role === 'user'
  const isSystem = line.role === 'system'
  const isTask = !isUser && !isSystem && /deadline/i.test(line.meta ?? '')

  const transition = { duration: 0.4, delay: 0.05 + index * 0.07, ease: EASE_OUT }
  const motionProps =
    reduced || reveal === 'none'
      ? {}
      : reveal === 'mount'
        ? {
            initial: { opacity: 0, y: 10, scale: 0.97 },
            animate: { opacity: 1, y: 0, scale: 1 },
            transition,
          }
        : {
            initial: { opacity: 0, y: 10, scale: 0.97 },
            whileInView: { opacity: 1, y: 0, scale: 1 },
            viewport: { once: true, amount: 0.6 },
            transition,
          }

  if (isSystem) {
    return (
      <motion.div className="flex justify-center py-0.5" {...motionProps}>
        <span className="rounded-full bg-white/[0.05] px-3 py-1 font-mono text-[0.6rem] uppercase tracking-[0.16em] text-muted">
          {line.text}
        </span>
      </motion.div>
    )
  }

  return (
    <motion.div className={`flex ${isUser ? 'justify-end' : 'justify-start'}`} {...motionProps}>
      <div
        className={`relative max-w-[80%] rounded-2xl px-3.5 py-2.5 text-[0.82rem] leading-snug ${
          isUser
            ? 'rounded-br-md bg-accent text-bg'
            : isTask
              ? 'rounded-bl-md border border-accent/30 bg-accent/[0.07] text-white'
              : 'rounded-bl-md border border-white/10 bg-white/[0.06] text-white'
        }`}
      >
        {isTask ? (
          <span className="mb-1 block font-mono text-[0.56rem] uppercase tracking-[0.18em] text-accent">
            Task
          </span>
        ) : null}
        <span>{line.text}</span>
        <span className="mt-1 flex items-center justify-end gap-0.5 text-[0.58rem] opacity-70">
          {line.meta && !/deadline/i.test(line.meta) ? line.meta : null}
          {isTask && line.meta ? <span className="text-accent">{line.meta}</span> : null}
          {isUser ? <TickIcon /> : null}
        </span>
      </div>
    </motion.div>
  )
}

function PhoneShell({
  screen,
  reveal = 'none',
  className = '',
}: {
  screen: PhoneScreen
  reveal?: RevealMode
  className?: string
}) {
  const reduced = useReducedMotion()

  return (
    <div className={`phone-hardware relative ${className}`}>
      <div className="phone-glow" aria-hidden />
      <div className="phone-frame relative overflow-hidden rounded-[2.6rem] border border-white/15 bg-[#050608] p-1.5 shadow-[0_50px_150px_rgba(0,0,0,0.7)]">
        <div className="phone-screen relative flex flex-col overflow-hidden rounded-[2.1rem] bg-[#070809]">
          <div className="pointer-events-none absolute inset-0 bg-[radial-gradient(circle_at_50%_-10%,rgba(74,222,128,0.12),transparent_42%)]" />

          {/* Status bar + dynamic island */}
          <div className="relative flex items-center justify-between px-5 pb-1 pt-3 text-white">
            <span className="font-mono text-[0.7rem] font-medium">9:41</span>
            <div className="absolute left-1/2 top-2.5 h-5 w-20 -translate-x-1/2 rounded-full bg-black" />
            <div className="flex items-center gap-1" aria-hidden>
              <span className="h-2 w-3.5 rounded-[2px] bg-white/80" />
              <span className="h-2 w-2 rounded-full bg-white/80" />
              <span className="h-2 w-4 rounded-[2px] bg-white/80" />
            </div>
          </div>

          {/* Chat header */}
          <div className="relative flex items-center gap-3 border-b border-white/8 px-4 pb-3 pt-2">
            <div className="flex h-9 w-9 items-center justify-center rounded-full bg-accent text-[0.72rem] font-black text-bg">
              H
            </div>
            <div className="min-w-0">
              <p className="flex items-center gap-1.5 text-[0.82rem] font-semibold text-white">
                HAP AI
                <span className="rounded bg-white/10 px-1 py-px font-mono text-[0.5rem] uppercase tracking-wider text-muted">
                  bot
                </span>
              </p>
              <p className="flex items-center gap-1.5 text-[0.62rem] text-accent">
                <motion.span
                  className="inline-block h-1.5 w-1.5 rounded-full bg-accent"
                  animate={reduced ? undefined : { opacity: [1, 0.4, 1] }}
                  transition={{ duration: 2.4, repeat: Infinity, ease: 'easeInOut' }}
                />
                online
              </p>
            </div>
          </div>

          {/* Messages */}
          <div className="relative flex-1 space-y-2.5 overflow-hidden px-3.5 py-4">
            <div className="mb-2 flex justify-center">
              <span className="rounded-full bg-white/[0.04] px-2.5 py-0.5 font-mono text-[0.56rem] uppercase tracking-[0.16em] text-muted">
                {screen.title}
              </span>
            </div>
            {screen.messages.map((line, index) => (
              <ChatBubble key={`${line.role}-${line.text}`} line={line} index={index} reveal={reveal} />
            ))}
          </div>

          {/* Input bar — makes it instantly recognizable as Telegram */}
          <div className="relative flex items-center gap-2 border-t border-white/8 px-3 py-2.5">
            <span className="text-muted" aria-hidden>
              <svg viewBox="0 0 24 24" className="h-4 w-4" fill="none" stroke="currentColor" strokeWidth="1.6">
                <path d="M21.4 11.1 12.3 20a4.5 4.5 0 0 1-6.4-6.4l8.5-8.5a3 3 0 0 1 4.2 4.2l-8.5 8.5a1.5 1.5 0 0 1-2.1-2.1l7.8-7.8" strokeLinecap="round" strokeLinejoin="round" />
              </svg>
            </span>
            <div className="flex-1 rounded-full bg-white/[0.06] px-3 py-1.5 text-[0.72rem] text-muted">
              Message
            </div>
            <span className="flex h-7 w-7 items-center justify-center rounded-full bg-accent text-bg" aria-hidden>
              <svg viewBox="0 0 24 24" className="h-3.5 w-3.5" fill="none" stroke="currentColor" strokeWidth="2">
                <path d="M5 12h13M12 5l7 7-7 7" strokeLinecap="round" strokeLinejoin="round" />
              </svg>
            </span>
          </div>
        </div>
      </div>
    </div>
  )
}

/* ---------- Sections ---------- */

function TopProgressBar() {
  const { scrollYProgress } = useScroll()
  const reduced = useReducedMotion()
  if (reduced) return null
  return (
    <motion.div
      className="fixed inset-x-0 top-0 z-[60] h-0.5 origin-left bg-accent"
      style={{ scaleX: scrollYProgress }}
      aria-hidden
    />
  )
}

function HeroSection({ screen }: { screen: PhoneScreen }) {
  const { t } = useTranslation()
  const botUrl = useBotUrl()
  const reduced = useReducedMotion()

  const scrollToStory = () => {
    document.getElementById('story')?.scrollIntoView({ behavior: reduced ? 'auto' : 'smooth' })
  }

  return (
    <section className="relative overflow-hidden pb-24 pt-12 md:pb-32 md:pt-20" aria-labelledby="hero-heading">
      <div className="hero-orb" aria-hidden />
      <Container className="relative">
        <div className="grid items-center gap-14 lg:grid-cols-[1.05fr_0.95fr] lg:gap-10">
          <div>
            <MotionReveal immediate>
              <span className="inline-flex items-center gap-2 rounded-full border border-white/10 bg-white/[0.03] px-3 py-1.5 font-mono text-[0.68rem] uppercase tracking-[0.18em] text-muted">
                <span className="inline-block h-1.5 w-1.5 rounded-full bg-accent" />
                {t('landing.story.hero.eyebrow')}
              </span>
            </MotionReveal>
            <MotionReveal immediate delay={0.05}>
              <h1
                id="hero-heading"
                className="font-heading mt-7 text-balance text-[3.4rem] font-semibold leading-[0.9] tracking-[-0.05em] text-white sm:text-[4.6rem] md:text-[5.6rem] lg:text-[6.2rem]"
              >
                {t('landing.story.hero.headline1')}
                <br />
                <span className="text-gradient">{t('landing.story.hero.headline2')}</span>
              </h1>
            </MotionReveal>
            <MotionReveal immediate delay={0.12}>
              <p className="mt-7 max-w-md text-pretty text-lg leading-relaxed text-muted">
                {t('landing.story.hero.subheadline')}
              </p>
            </MotionReveal>
            <MotionReveal immediate delay={0.18}>
              <div className="mt-9 flex flex-col items-start gap-3.5">
                <span className="inline-flex items-center gap-2 rounded-full border border-accent/30 bg-accent/[0.08] px-3 py-1 font-mono text-[0.62rem] uppercase tracking-[0.16em] text-accent">
                  <span className="inline-block h-1.5 w-1.5 rounded-full bg-accent" />
                  {t('landing.story.hero.betaBadge')}
                </span>
                <div className="flex flex-wrap items-center gap-x-5 gap-y-3">
                  <Button href={botUrl} telegramBot className="rounded-full px-7 py-3 text-base">
                    {t('landing.ctaPrimary')}
                  </Button>
                  <button
                    type="button"
                    onClick={scrollToStory}
                    className="focus-ring group inline-flex items-center gap-2 rounded-full px-1 py-2 text-sm font-medium text-muted transition-colors hover:text-white"
                  >
                    {t('landing.story.hero.ctaSecondary')}
                    <span aria-hidden className="transition-transform group-hover:translate-y-0.5">↓</span>
                  </button>
                </div>
              </div>
            </MotionReveal>
            <MotionReveal immediate delay={0.24}>
              <p className="mt-7 font-mono text-[0.7rem] uppercase tracking-[0.16em] text-muted/70">
                {t('landing.story.hero.trust')}
              </p>
            </MotionReveal>
          </div>

          <motion.div
            className="relative flex justify-center lg:justify-end"
            initial={reduced ? false : { opacity: 0, y: 44, rotate: -2.5, scale: 0.93 }}
            animate={{ opacity: 1, y: 0, rotate: 0, scale: 1 }}
            transition={{ duration: 0.95, delay: 0.15, ease: EASE_OUT }}
          >
            <PhoneShell screen={screen} reveal="mount" className="w-[18.5rem] sm:w-[20rem]" />
          </motion.div>
        </div>
      </Container>
    </section>
  )
}

function ContrastBand() {
  const { t } = useTranslation()
  return (
    <section className="border-y border-white/8 bg-white/[0.015] py-16 md:py-20" aria-label={t('landing.story.contrast.eyebrow')}>
      <Container>
        <MotionReveal className="mx-auto max-w-4xl text-center">
          <p className="font-mono text-xs uppercase tracking-[0.28em] text-accent">
            {t('landing.story.contrast.eyebrow')}
          </p>
          <p className="font-heading mt-6 text-3xl font-semibold leading-tight tracking-[-0.03em] text-white sm:text-4xl md:text-5xl">
            <span className="text-muted">{t('landing.story.contrast.them')}</span>{' '}
            {t('landing.story.contrast.us')}
          </p>
        </MotionReveal>
      </Container>
    </section>
  )
}

function FocusStatement() {
  const { t } = useTranslation()
  const ref = useRef<HTMLElement>(null)
  const reduced = useReducedMotion()
  const { scrollYProgress } = useScroll({ target: ref, offset: ['start end', 'end start'] })
  const opacity = useTransform(scrollYProgress, [0.05, 0.32, 0.7, 0.95], [0, 1, 1, 0])
  const scale = useTransform(scrollYProgress, [0.05, 0.4, 0.7, 0.95], [0.96, 1, 1, 0.97])
  const filter = useTransform(scrollYProgress, [0.05, 0.32, 0.7, 0.95], [
    'blur(14px)',
    'blur(0px)',
    'blur(0px)',
    'blur(10px)',
  ])

  return (
    <section
      ref={ref}
      className="relative flex min-h-[78svh] items-center py-24"
      aria-labelledby="problem-heading"
    >
      <Container>
        <motion.div
          className="mx-auto max-w-5xl text-center"
          style={reduced ? undefined : { opacity, scale, filter }}
        >
          <p className="font-mono text-xs uppercase tracking-[0.28em] text-accent">
            {t('landing.story.problem.eyebrow')}
          </p>
          <h2
            id="problem-heading"
            className="font-heading mt-7 text-balance text-4xl font-semibold leading-[0.98] tracking-[-0.05em] text-white sm:text-6xl md:text-7xl lg:text-[6.5rem]"
          >
            {t('landing.story.problem.headline')}{' '}
            <span className="text-gradient">{t('landing.story.problem.accent')}</span>
          </h2>
          <p className="mt-8 text-base text-muted md:text-lg">{t('landing.story.problem.sub')}</p>
        </motion.div>
      </Container>
    </section>
  )
}

function ChapterText({ index }: { index: number }) {
  const { t } = useTranslation()
  const key = CHAPTER_KEYS[index]
  return (
    <>
      <p className="font-mono text-xs uppercase tracking-[0.26em] text-accent">
        {String(index + 1).padStart(2, '0')} — {t(`landing.story.scrolly.${key}.eyebrow`)}
      </p>
      <h3 className="font-heading mt-5 text-balance text-4xl font-semibold leading-[1] tracking-[-0.045em] text-white sm:text-5xl md:text-6xl">
        {t(`landing.story.scrolly.${key}.headline`)}
      </h3>
      <p className="mt-5 max-w-md text-pretty text-lg leading-relaxed text-muted">
        {t(`landing.story.scrolly.${key}.body`)}
      </p>
    </>
  )
}

function PhoneCrossfadeLayer({
  screen,
  index,
  total,
  progress,
}: {
  screen: PhoneScreen
  index: number
  total: number
  progress: MotionValue<number>
}) {
  const start = index / total
  const end = (index + 1) / total
  // Keep every offset inside [0,1] and strictly increasing — the Web Animations
  // API throws (and unmounts the whole tree) on out-of-range / non-monotonic offsets.
  const a = clamp01(start - 0.05)
  const b = clamp01(Math.max(a + 0.001, start + 0.05))
  const c = clamp01(Math.max(b + 0.001, end - 0.05))
  const d = clamp01(Math.max(c + 0.001, end + 0.05))
  const range = [a, b, c, d]
  // First screen starts visible, last screen stays visible at the end — so the
  // phone is never blank at the scroll boundaries.
  const firstIn = index === 0 ? 1 : 0
  const lastOut = index === total - 1 ? 1 : 0
  const opacity = useTransform(progress, range, [firstIn, 1, 1, lastOut])
  const scale = useTransform(progress, range, [index === 0 ? 1 : 0.96, 1, 1, index === total - 1 ? 1 : 0.97])
  const filter = useTransform(progress, range, [
    index === 0 ? 'blur(0px)' : 'blur(10px)',
    'blur(0px)',
    'blur(0px)',
    index === total - 1 ? 'blur(0px)' : 'blur(8px)',
  ])

  return (
    <motion.div className="absolute inset-0 flex items-center justify-center" style={{ opacity, scale, filter }}>
      <PhoneShell screen={screen} className="w-[19rem]" />
    </motion.div>
  )
}

function StoryDot({
  index,
  total,
  progress,
}: {
  index: number
  total: number
  progress: MotionValue<number>
}) {
  const center = (index + 0.5) / total
  const half = 0.5 / total
  const a = clamp01(center - half)
  const b = clamp01(center)
  const c = clamp01(center + half)
  const opacity = useTransform(progress, [a, b, c], [0.28, 1, 0.28])
  const width = useTransform(progress, [a, b, c], ['0.75rem', '2.25rem', '0.75rem'])
  return <motion.span className="h-1.5 rounded-full bg-accent" style={{ width, opacity }} />
}

function StickyPhoneStory({ screens }: { screens: PhoneScreen[] }) {
  const { t } = useTranslation()
  const ref = useRef<HTMLDivElement>(null)
  const { scrollYProgress } = useScroll({ target: ref, offset: ['start start', 'end end'] })

  return (
    <section id="story" ref={ref} className="relative" aria-labelledby="story-heading">
      <h2 id="story-heading" className="sr-only">
        {t('landing.story.storyTitle')}
      </h2>

      {/* Desktop: sticky phone, scroll-driven crossfade between conversations */}
      <div className="hidden lg:block">
        <Container>
          <div className="grid grid-cols-[1fr_0.95fr] gap-16">
            <div>
              {CHAPTER_KEYS.map((key, index) => (
                <div key={key} className="flex min-h-[88svh] flex-col justify-center">
                  <MotionReveal className="max-w-xl">
                    <ChapterText index={index} />
                  </MotionReveal>
                </div>
              ))}
            </div>

            <div className="relative">
              <div className="sticky top-0 flex h-[100svh] items-center justify-center">
                <div className="relative h-[clamp(28rem,calc(100svh-9rem),37rem)] w-[19rem]">
                  {screens.map((screen, index) => (
                    <PhoneCrossfadeLayer
                      key={screen.title}
                      screen={screen}
                      index={index}
                      total={screens.length}
                      progress={scrollYProgress}
                    />
                  ))}
                </div>
                <div className="absolute inset-x-0 bottom-7 flex justify-center gap-2">
                  {screens.map((screen, index) => (
                    <StoryDot
                      key={screen.title}
                      index={index}
                      total={screens.length}
                      progress={scrollYProgress}
                    />
                  ))}
                </div>
              </div>
            </div>
          </div>
        </Container>
      </div>

      {/* Mobile: narrated sequence — caption + the actual phone screen, in order */}
      <div className="lg:hidden">
        <Container>
          <div className="space-y-24 py-20">
            {CHAPTER_KEYS.map((key, index) => (
              <div key={key}>
                <MotionReveal>
                  <ChapterText index={index} />
                </MotionReveal>
                <MotionReveal delay={0.1} className="mt-10 flex justify-center">
                  <div className="w-full max-w-[19rem]">
                    <PhoneShell screen={screens[index] ?? screens[0]} reveal="inview" className="w-full" />
                    {(screens[index] ?? screens[0]).footer ? (
                      <p className="mt-4 text-center font-mono text-[0.66rem] uppercase tracking-[0.14em] text-muted">
                        {(screens[index] ?? screens[0]).footer}
                      </p>
                    ) : null}
                  </div>
                </MotionReveal>
              </div>
            ))}
          </div>
        </Container>
      </div>
    </section>
  )
}

function CapabilityTypography() {
  const { t } = useTranslation()
  const ref = useRef<HTMLElement>(null)
  const { scrollYProgress } = useScroll({ target: ref, offset: ['start end', 'end start'] })
  const glowY = useTransform(scrollYProgress, [0, 1], ['-20%', '20%'])

  return (
    <section ref={ref} id="what-hap-does" className="relative overflow-hidden py-28 md:py-40" aria-labelledby="what-heading">
      <motion.div
        className="pointer-events-none absolute inset-x-0 top-1/3 h-72 bg-accent/8 blur-3xl"
        style={{ y: glowY }}
        aria-hidden
      />
      <Container>
        <MotionReveal>
          <p className="font-mono text-xs uppercase tracking-[0.28em] text-accent">
            {t('landing.story.what.eyebrow')}
          </p>
          <h2 id="what-heading" className="sr-only">
            {t('landing.story.what.eyebrow')}
          </h2>
        </MotionReveal>
        <div className="mt-10 border-t border-white/10">
          {CAPABILITY_KEYS.map((key, index) => (
            <MotionReveal key={key} delay={index * 0.05}>
              <div className="group flex items-baseline gap-5 border-b border-white/10 py-8 md:gap-10 md:py-10">
                <span className="font-mono text-xs text-accent md:text-sm">
                  {String(index + 1).padStart(2, '0')}
                </span>
                <p className="font-heading text-balance text-4xl font-semibold leading-[0.98] tracking-[-0.05em] text-white sm:text-5xl md:text-7xl">
                  {t(`landing.story.what.${key}`)}
                </p>
              </div>
            </MotionReveal>
          ))}
        </div>
        <MotionReveal delay={0.1}>
          <p className="mt-10 max-w-md text-lg text-muted">{t('landing.story.what.kicker')}</p>
        </MotionReveal>
      </Container>
    </section>
  )
}

function FounderJourney() {
  const { t } = useTranslation()
  const ref = useRef<HTMLElement>(null)
  const reduced = useReducedMotion()
  const { scrollYProgress } = useScroll({ target: ref, offset: ['start 80%', 'end 60%'] })
  const lineScaleX = useTransform(scrollYProgress, [0, 1], [0, 1])

  return (
    <section ref={ref} className="relative py-28 md:py-40" aria-labelledby="journey-heading">
      <Container>
        <MotionReveal className="mx-auto max-w-3xl text-center">
          <p className="font-mono text-xs uppercase tracking-[0.28em] text-accent">
            {t('landing.story.journey.eyebrow')}
          </p>
          <h2
            id="journey-heading"
            className="font-heading mt-6 text-balance text-4xl font-semibold leading-[0.98] tracking-[-0.05em] text-white sm:text-6xl md:text-7xl"
          >
            {t('landing.story.journey.title')}
          </h2>
        </MotionReveal>

        <div className="relative mx-auto mt-20 max-w-6xl">
          <div className="absolute left-0 right-0 top-7 hidden h-px bg-white/10 md:block" aria-hidden />
          <motion.div
            className="absolute left-0 right-0 top-7 hidden h-px origin-left bg-accent md:block"
            style={reduced ? { transform: 'scaleX(1)' } : { scaleX: lineScaleX }}
            aria-hidden
          />
          <ol className="grid gap-6 md:grid-cols-5">
            {JOURNEY_KEYS.map((key, index) => (
              <MotionReveal key={key} delay={index * 0.08}>
                <li className="relative rounded-3xl border border-white/10 bg-white/[0.025] p-6 md:rounded-none md:border-0 md:bg-transparent md:p-0">
                  <motion.div
                    className="flex h-14 w-14 items-center justify-center rounded-full border border-accent/40 bg-bg font-mono text-sm font-semibold text-accent shadow-[0_0_40px_rgba(74,222,128,0.18)]"
                    initial={reduced ? false : { scale: 0.7, opacity: 0 }}
                    whileInView={{ scale: 1, opacity: 1 }}
                    viewport={{ once: true, amount: 0.7 }}
                    transition={{ duration: DURATION.medium, delay: 0.15 + index * 0.09, ease: EASE_OUT }}
                  >
                    {String(index + 1).padStart(2, '0')}
                  </motion.div>
                  <p className="font-heading mt-5 text-2xl font-semibold tracking-[-0.035em] text-white">
                    {t(`landing.story.journey.${key}`)}
                  </p>
                  <p className="mt-2.5 text-sm leading-relaxed text-muted">
                    {t(`landing.story.journeyNotes.${key}`)}
                  </p>
                </li>
              </MotionReveal>
            ))}
          </ol>
        </div>
      </Container>
    </section>
  )
}

function BetaSection() {
  const { t } = useTranslation()
  const available = getStringList(t('landing.story.beta.available', { returnObjects: true }))
  const coming = getStringList(t('landing.story.beta.coming', { returnObjects: true }))

  return (
    <section className="relative py-28 md:py-36" aria-labelledby="beta-heading">
      <Container>
        <MotionReveal className="mx-auto max-w-3xl text-center">
          <span className="inline-flex items-center gap-2 rounded-full border border-accent/30 bg-accent/[0.08] px-3 py-1.5 font-mono text-[0.68rem] uppercase tracking-[0.18em] text-accent">
            <span className="inline-block h-1.5 w-1.5 rounded-full bg-accent" />
            {t('landing.story.beta.eyebrow')}
          </span>
          <h2
            id="beta-heading"
            className="font-heading mt-7 text-balance text-3xl font-semibold leading-[1.02] tracking-[-0.04em] text-white sm:text-5xl md:text-6xl"
          >
            {t('landing.story.beta.headline')}
          </h2>
          <p className="mx-auto mt-6 max-w-2xl text-pretty text-base leading-relaxed text-muted md:text-lg">
            {t('landing.story.beta.body')}
          </p>
        </MotionReveal>

        <div className="mx-auto mt-14 grid max-w-4xl gap-6 md:grid-cols-2">
          <MotionReveal>
            <div className="h-full rounded-3xl border border-white/10 bg-white/[0.025] p-8">
              <p className="font-mono text-xs uppercase tracking-[0.2em] text-accent">
                {t('landing.story.beta.availableTitle')}
              </p>
              <ul className="mt-6 space-y-4">
                {available.map((item) => (
                  <li key={item} className="flex items-start gap-3 text-[0.95rem] leading-snug text-white">
                    <svg viewBox="0 0 20 20" className="mt-0.5 h-4 w-4 shrink-0 text-accent" fill="none" aria-hidden>
                      <circle cx="10" cy="10" r="9" stroke="currentColor" strokeWidth="1.4" opacity="0.4" />
                      <path d="M6 10.5l2.5 2.5L14 7.5" stroke="currentColor" strokeWidth="1.7" strokeLinecap="round" strokeLinejoin="round" />
                    </svg>
                    {item}
                  </li>
                ))}
              </ul>
            </div>
          </MotionReveal>

          <MotionReveal delay={0.08}>
            <div className="h-full rounded-3xl border border-dashed border-white/12 bg-transparent p-8">
              <p className="font-mono text-xs uppercase tracking-[0.2em] text-muted">
                {t('landing.story.beta.comingTitle')}
              </p>
              <ul className="mt-6 space-y-4">
                {coming.map((item) => (
                  <li key={item} className="flex items-start gap-3 text-[0.95rem] leading-snug text-muted">
                    <span aria-hidden className="mt-0.5 shrink-0 font-mono text-accent/70">→</span>
                    {item}
                  </li>
                ))}
              </ul>
            </div>
          </MotionReveal>
        </div>
      </Container>
    </section>
  )
}

function FinalCTA({ screen }: { screen: PhoneScreen }) {
  const { t } = useTranslation()
  const botUrl = useBotUrl()
  const reduced = useReducedMotion()

  return (
    <section className="relative overflow-hidden py-28 md:py-44" aria-labelledby="cta-heading">
      <div className="pointer-events-none absolute left-1/2 top-1/2 h-[28rem] w-[28rem] -translate-x-1/2 -translate-y-1/2 rounded-full bg-accent/10 blur-[120px]" aria-hidden />
      <Container className="relative">
        <div className="grid items-center gap-14 lg:grid-cols-[1.1fr_0.9fr]">
          <div className="text-center lg:text-left">
            <MotionReveal>
              <h2
                id="cta-heading"
                className="font-heading text-balance text-5xl font-semibold leading-[0.95] tracking-[-0.05em] text-white sm:text-6xl md:text-7xl"
              >
                {t('landing.story.final.headline1')}
                <br />
                <span className="text-gradient">{t('landing.story.final.headline2')}</span>
              </h2>
            </MotionReveal>
            <MotionReveal delay={0.08}>
              <p className="mt-7 text-lg text-muted">{t('landing.story.final.sub')}</p>
            </MotionReveal>
            <MotionReveal delay={0.14}>
              <div className="mt-10 flex flex-wrap justify-center gap-4 lg:justify-start">
                <Button href={botUrl} telegramBot className="rounded-full px-8 py-3.5 text-base">
                  {t('landing.story.final.button')}
                </Button>
              </div>
              <p className="mt-6 font-mono text-[0.7rem] uppercase tracking-[0.16em] text-muted/70">
                {t('landing.story.hero.trust')}
              </p>
            </MotionReveal>
          </div>

          <motion.div
            className="hidden justify-center lg:flex"
            initial={reduced ? false : { opacity: 0, y: 36, scale: 0.94 }}
            whileInView={{ opacity: 1, y: 0, scale: 1 }}
            viewport={{ once: true, amount: 0.4 }}
            transition={{ duration: 0.8, ease: EASE_OUT }}
          >
            <PhoneShell screen={screen} className="w-[18rem]" />
          </motion.div>
        </div>
      </Container>
    </section>
  )
}

export default function Landing() {
  const { t } = useTranslation()

  const heroScreen = getPhoneScreen(t('landing.story.hero.phone', { returnObjects: true }), FALLBACK_HERO_SCREEN)
  const phoneScreens = getPhoneScreens(t('landing.story.phoneScreens', { returnObjects: true }))
  const finalScreen = phoneScreens[phoneScreens.length - 1] ?? heroScreen

  return (
    <div className="cinematic-bg min-h-screen overflow-x-clip pb-20 sm:pb-0">
      <TopProgressBar />
      <Header />
      <main>
        <HeroSection screen={heroScreen} />
        <ContrastBand />
        <FocusStatement />
        <StickyPhoneStory screens={phoneScreens} />
        <CapabilityTypography />
        <FounderJourney />
        <BetaSection />
        <FinalCTA screen={finalScreen} />
      </main>
      <Footer />
      <MobileCTA />

      {import.meta.env.DEV && import.meta.env.VITE_SENTRY_DSN ? <SentryErrorButton /> : null}
    </div>
  )
}
