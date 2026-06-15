import { useTranslation } from 'react-i18next'
import Button from '../../shared/components/Button'
import Container from '../../shared/components/Container'
import HoverCard from '../../shared/components/HoverCard'
import { useBotUrl } from '../../shared/hooks/useBotUrl'
import MotionReveal from '../../shared/motion/MotionReveal'

export default function FinalCTASection() {
  const { t } = useTranslation()
  const botUrl = useBotUrl()

  return (
    <section className="section-divider section-padding">
      <Container className="text-center">
        <MotionReveal>
          <HoverCard className="card mx-auto max-w-3xl px-8 py-20 md:px-16 md:py-24" glow>
            <h2 className="font-heading text-3xl font-semibold text-white sm:text-4xl md:text-5xl">
              {t('landing.finalCta.headline1')}
              <br />
              <span className="text-accent">{t('landing.finalCta.headline2')}</span>
            </h2>
            <div className="mt-12">
              <Button href={botUrl} className="px-8 py-3 text-base">
                {t('landing.finalCta.button')}
              </Button>
            </div>
          </HoverCard>
        </MotionReveal>
      </Container>
    </section>
  )
}
