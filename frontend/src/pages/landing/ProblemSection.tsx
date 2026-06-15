import { useTranslation } from 'react-i18next'
import Container from '../../shared/components/Container'
import HoverCard from '../../shared/components/HoverCard'
import MotionReveal from '../../shared/motion/MotionReveal'
import { MotionStagger, MotionStaggerItem } from '../../shared/motion/MotionReveal'

type ComparisonCardProps = {
  title: string
  lines: string[]
  variant: 'muted' | 'highlight'
}

function ComparisonCard({ title, lines, variant }: ComparisonCardProps) {
  const isHighlight = variant === 'highlight'

  return (
    <HoverCard
      className={isHighlight ? 'card-highlight p-8' : 'card p-8'}
      glow={isHighlight}
    >
      <h3
        className={`font-mono text-[10px] font-medium uppercase tracking-[0.14em] ${
          isHighlight ? 'text-accent' : 'text-muted'
        }`}
      >
        {title}
      </h3>
      <div className="mt-6 space-y-2.5">
        {lines.map((line) => (
          <p
            key={line}
            className={`text-sm leading-relaxed ${isHighlight ? 'text-white' : 'text-muted'}`}
          >
            {line}
          </p>
        ))}
      </div>
    </HoverCard>
  )
}

export default function ProblemSection() {
  const { t } = useTranslation()

  const cards: ComparisonCardProps[] = [
    {
      title: t('landing.problem.genericAi.title'),
      lines: [t('landing.problem.genericAi.line1'), t('landing.problem.genericAi.line2')],
      variant: 'muted',
    },
    {
      title: t('landing.problem.consultants.title'),
      lines: [t('landing.problem.consultants.line1'), t('landing.problem.consultants.line2')],
      variant: 'muted',
    },
    {
      title: t('landing.problem.hap.title'),
      lines: [
        t('landing.problem.hap.line1'),
        t('landing.problem.hap.line2'),
        t('landing.problem.hap.line3'),
      ],
      variant: 'highlight',
    },
  ]

  return (
    <section className="section-divider section-padding">
      <Container>
        <MotionReveal>
          <h2 className="font-heading max-w-2xl text-3xl font-semibold text-white sm:text-4xl">
            {t('landing.problem.headline')}
          </h2>
        </MotionReveal>
        <MotionStagger className="mt-16 grid gap-4 md:grid-cols-3">
          {cards.map((card) => (
            <MotionStaggerItem key={card.title}>
              <ComparisonCard {...card} />
            </MotionStaggerItem>
          ))}
        </MotionStagger>
      </Container>
    </section>
  )
}
