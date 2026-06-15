import { useTranslation } from 'react-i18next'
import { motion, useReducedMotion } from 'framer-motion'
import Container from '../../shared/components/Container'
import HoverCard from '../../shared/components/HoverCard'
import MotionReveal from '../../shared/motion/MotionReveal'
import { EASE_OUT, DURATION } from '../../shared/motion/presets'

const STEP_KEYS = ['step1', 'step2', 'step3', 'step4', 'step5'] as const

export default function HowItWorksSection() {
  const { t } = useTranslation()
  const reduced = useReducedMotion()

  return (
    <section id="how-it-works" className="section-divider section-padding bg-surface">
      <Container>
        <MotionReveal className="text-center">
          <h2 className="font-heading text-3xl font-semibold text-white sm:text-4xl">
            {t('landing.howItWorks.title')}
          </h2>
        </MotionReveal>

        <ol className="relative mx-auto mt-20 max-w-3xl space-y-0">
          {STEP_KEYS.map((key, index) => {
            const isLast = index === STEP_KEYS.length - 1
            return (
              <MotionReveal key={key} delay={index * 0.08}>
                <li className="relative flex gap-6 pb-14 last:pb-0 md:gap-8">
                  {!isLast && (
                    <motion.div
                      className="absolute left-[11px] top-8 hidden h-[calc(100%-1.5rem)] w-px origin-top bg-border md:left-[11px] md:block"
                      initial={reduced ? false : { scaleY: 0 }}
                      whileInView={{ scaleY: 1 }}
                      viewport={{ once: true, amount: 0.5 }}
                      transition={{ duration: DURATION.slow, delay: 0.15 + index * 0.1, ease: EASE_OUT }}
                      aria-hidden
                    />
                  )}
                  <div className="relative z-10 flex h-6 w-6 shrink-0 items-center justify-center rounded-sm border border-border bg-bg font-mono text-[10px] font-medium text-accent">
                    {index + 1}
                  </div>
                  <HoverCard className="card min-w-0 flex-1 p-6 md:p-8">
                    <h3 className="font-heading text-lg font-semibold text-white">
                      {t(`landing.howItWorks.${key}.title`)}
                    </h3>
                    <p className="mt-3 text-sm leading-relaxed text-muted md:text-base">
                      {t(`landing.howItWorks.${key}.body`)}
                    </p>
                  </HoverCard>
                </li>
              </MotionReveal>
            )
          })}
        </ol>
      </Container>
    </section>
  )
}
