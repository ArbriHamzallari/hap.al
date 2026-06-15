import type { ReactNode } from 'react'
import { useTranslation } from 'react-i18next'
import Container from '../../shared/components/Container'
import HoverCard from '../../shared/components/HoverCard'
import MotionReveal from '../../shared/motion/MotionReveal'
import { MotionStagger, MotionStaggerItem } from '../../shared/motion/MotionReveal'

const CARD_KEYS = ['challenge', 'plans', 'tasks', 'accountability'] as const

type IconName = (typeof CARD_KEYS)[number]

function FeatureIcon({ name }: { name: IconName }) {
  const paths: Record<IconName, ReactNode> = {
    challenge: (
      <>
        <circle cx="12" cy="12" r="9" />
        <circle cx="12" cy="12" r="5" />
        <circle cx="12" cy="12" r="1.5" fill="currentColor" stroke="none" />
        <path d="M12 3v2M12 19v2M3 12h2M19 12h2" />
      </>
    ),
    plans: (
      <>
        <path d="M5 7h14M5 12h10M5 17h6" />
        <path d="M17 12l2 2 4-4" />
      </>
    ),
    tasks: (
      <>
        <rect x="4" y="5" width="16" height="16" rx="1" />
        <path d="M8 10h8M8 14h5" />
        <path d="M16 3v4M8 3v4M4 9h16" />
      </>
    ),
    accountability: (
      <>
        <path d="M4 18v-8M10 18V6M16 18v-5M22 18V9" />
        <path d="M3 18h19" />
      </>
    ),
  }

  return (
    <div className="flex h-10 w-10 items-center justify-center rounded-sm border border-accent/20 bg-accent/5 text-accent">
      <svg
        viewBox="0 0 24 24"
        fill="none"
        stroke="currentColor"
        strokeWidth="1.5"
        strokeLinecap="round"
        strokeLinejoin="round"
        className="h-5 w-5"
        aria-hidden
      >
        {paths[name]}
      </svg>
    </div>
  )
}

export default function WhatHapDoesSection() {
  const { t } = useTranslation()

  return (
    <section id="what-hap-does" className="section-divider section-padding">
      <Container>
        <MotionReveal className="mx-auto max-w-2xl text-center">
          <h2 className="font-heading text-3xl font-semibold text-white sm:text-4xl">
            {t('landing.whatHapDoes.title')}
          </h2>
          <p className="mt-5 text-lg text-white">{t('landing.whatHapDoes.subtitle1')}</p>
          <p className="mt-2 text-muted">{t('landing.whatHapDoes.subtitle2')}</p>
        </MotionReveal>

        <MotionStagger className="mt-16 grid gap-4 sm:grid-cols-2">
          {CARD_KEYS.map((key) => (
            <MotionStaggerItem key={key}>
              <HoverCard className="card group h-full p-8 transition-colors duration-150 hover:border-accent/20">
                <FeatureIcon name={key} />
                <h3 className="font-heading mt-6 text-lg font-semibold text-white">
                  {t(`landing.whatHapDoes.cards.${key}.title`)}
                </h3>
                <p className="mt-3 text-sm leading-relaxed text-muted md:text-base">
                  {t(`landing.whatHapDoes.cards.${key}.body`)}
                </p>
              </HoverCard>
            </MotionStaggerItem>
          ))}
        </MotionStagger>
      </Container>
    </section>
  )
}
