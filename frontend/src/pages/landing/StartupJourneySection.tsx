import { useState } from 'react'
import { useTranslation } from 'react-i18next'
import { AnimatePresence, motion, useReducedMotion } from 'framer-motion'
import Container from '../../shared/components/Container'
import MotionReveal from '../../shared/motion/MotionReveal'
import { EASE_OUT, panelSwap } from '../../shared/motion/presets'

const STAGE_KEYS = ['idea', 'validation', 'customers', 'mvp', 'launch', 'growth'] as const
type StageKey = (typeof STAGE_KEYS)[number]

export default function StartupJourneySection() {
  const { t } = useTranslation()
  const [active, setActive] = useState<StageKey>('idea')
  const reduced = useReducedMotion()

  const tasks = t(`landing.journey.stages.${active}.tasks`, { returnObjects: true }) as string[]

  return (
    <section className="section-divider section-padding">
      <Container>
        <MotionReveal className="text-center">
          <h2 className="font-heading text-3xl font-semibold text-white sm:text-4xl">
            {t('landing.journey.title')}
          </h2>
          <p className="mx-auto mt-5 max-w-xl text-muted">{t('landing.journey.subtitle')}</p>
        </MotionReveal>

        <MotionReveal delay={0.1} className="mt-16 overflow-x-auto pb-1">
          <div className="flex min-w-max items-center justify-center gap-0 md:min-w-0">
            {STAGE_KEYS.map((key, index) => {
              const isActive = active === key
              const isPast = STAGE_KEYS.indexOf(active) > index
              return (
                <div key={key} className="flex items-center">
                  <motion.button
                    type="button"
                    onClick={() => setActive(key)}
                    aria-pressed={isActive}
                    className={`focus-ring relative rounded-sm px-4 py-2 text-sm font-medium ${
                      isActive
                        ? 'text-white'
                        : isPast
                          ? 'text-accent'
                          : 'text-muted hover:text-white'
                    }`}
                    whileHover={reduced ? undefined : { scale: 1.02 }}
                    whileTap={reduced ? undefined : { scale: 0.98 }}
                    transition={{ type: 'spring', stiffness: 400, damping: 28 }}
                  >
                    {isActive && !reduced && (
                      <motion.span
                        layoutId="journey-stage"
                        className="absolute inset-0 rounded-sm bg-card ring-1 ring-accent/30"
                        style={{ zIndex: -1 }}
                        transition={{ type: 'spring', stiffness: 380, damping: 32 }}
                      />
                    )}
                    {isActive && reduced && (
                      <span
                        className="absolute inset-0 rounded-sm bg-card ring-1 ring-accent/30"
                        style={{ zIndex: -1 }}
                      />
                    )}
                    {t(`landing.journey.stages.${key}.label`)}
                  </motion.button>
                  {index < STAGE_KEYS.length - 1 && (
                    <motion.div
                      className="mx-0.5 hidden h-px w-8 md:block lg:w-12"
                      animate={{
                        backgroundColor: isPast
                          ? 'rgba(74, 222, 128, 0.3)'
                          : 'rgba(255, 255, 255, 0.08)',
                      }}
                      transition={{ duration: 0.3, ease: EASE_OUT }}
                      aria-hidden
                    />
                  )}
                </div>
              )
            })}
          </div>
        </MotionReveal>

        <div className="mx-auto mt-12 max-w-2xl">
          <AnimatePresence mode="wait">
            <motion.div
              key={active}
              className="card p-8 md:p-10"
              initial={reduced ? false : panelSwap.initial}
              animate={panelSwap.animate}
              exit={reduced ? undefined : panelSwap.exit}
              transition={panelSwap.transition}
            >
              <p className="font-mono text-[10px] uppercase tracking-[0.14em] text-accent">
                {t(`landing.journey.stages.${active}.label`)}
              </p>
              <ul className="mt-8 space-y-5">
                {tasks.map((task, i) => (
                  <motion.li
                    key={task}
                    className="flex gap-4 text-sm leading-relaxed text-white md:text-base"
                    initial={reduced ? false : { opacity: 0, x: -8 }}
                    animate={{ opacity: 1, x: 0 }}
                    transition={{ duration: 0.35, delay: 0.08 + i * 0.06, ease: EASE_OUT }}
                  >
                    <span className="mt-0.5 flex h-5 w-5 shrink-0 items-center justify-center rounded-sm border border-border bg-surface font-mono text-[10px] text-accent">
                      {i + 1}
                    </span>
                    {task}
                  </motion.li>
                ))}
              </ul>
            </motion.div>
          </AnimatePresence>
        </div>
      </Container>
    </section>
  )
}
