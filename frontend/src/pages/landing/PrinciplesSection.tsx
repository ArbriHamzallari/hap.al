import { useTranslation } from 'react-i18next'
import Container from '../../shared/components/Container'
import HoverCard from '../../shared/components/HoverCard'
import MotionReveal from '../../shared/motion/MotionReveal'
import { MotionStagger, MotionStaggerItem } from '../../shared/motion/MotionReveal'

const PRINCIPLE_KEYS = ['noFake', 'execution', 'focus', 'momentum'] as const

export default function PrinciplesSection() {
  const { t } = useTranslation()

  return (
    <section className="section-divider section-padding">
      <Container>
        <MotionReveal className="text-center">
          <h2 className="font-heading text-3xl font-semibold text-white sm:text-4xl">
            {t('landing.principles.title')}
          </h2>
        </MotionReveal>

        <MotionStagger className="mt-16 grid gap-4 sm:grid-cols-2">
          {PRINCIPLE_KEYS.map((key) => (
            <MotionStaggerItem key={key}>
              <HoverCard className="card p-8 transition-colors duration-150 hover:border-border-strong">
                <h3 className="font-heading text-lg font-semibold text-white">
                  {t(`landing.principles.${key}.title`)}
                </h3>
                <p className="mt-4 text-sm leading-relaxed text-muted md:text-base">
                  {t(`landing.principles.${key}.body`)}
                </p>
              </HoverCard>
            </MotionStaggerItem>
          ))}
        </MotionStagger>
      </Container>
    </section>
  )
}
