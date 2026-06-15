import { useTranslation } from 'react-i18next'
import Button from '../../shared/components/Button'
import Container from '../../shared/components/Container'
import { HeroChatMockup } from '../../shared/components/TelegramMockup'
import { useBotUrl } from '../../shared/hooks/useBotUrl'
import MotionReveal from '../../shared/motion/MotionReveal'

export default function HeroSection() {
  const { t } = useTranslation()
  const botUrl = useBotUrl()

  const scrollToWhatHapDoes = () => {
    document.getElementById('what-hap-does')?.scrollIntoView({ behavior: 'smooth' })
  }

  return (
    <section className="section-padding">
      <Container>
        <div className="grid items-center gap-16 lg:grid-cols-2 lg:gap-20">
          <MotionReveal immediate>
            <span className="badge">{t('landing.badge')}</span>
            <h1 className="font-heading mt-8 text-4xl font-semibold leading-[1.08] text-white sm:text-5xl lg:text-[3.5rem]">
              {t('landing.headline1')}
              <br />
              <span className="text-accent">{t('landing.headline2')}</span>
            </h1>
            <p className="mt-7 max-w-lg text-base font-medium leading-relaxed text-white lg:text-lg">
              {t('landing.subheadline')}
            </p>
            <p className="mt-4 max-w-lg text-sm leading-relaxed text-muted lg:text-base">
              {t('landing.heroSupport')}
            </p>
            <div className="mt-10 flex flex-wrap gap-3">
              <Button href={botUrl}>{t('landing.ctaPrimary')}</Button>
              <Button variant="secondary" onClick={scrollToWhatHapDoes}>
                {t('landing.ctaSecondary')}
              </Button>
            </div>
          </MotionReveal>

          <MotionReveal immediate delay={0.15} className="flex justify-center lg:justify-end">
            <HeroChatMockup
              sender={t('landing.heroChat.sender')}
              line1={t('landing.heroChat.line1')}
              line2={t('landing.heroChat.line2')}
              taskLabel={t('landing.heroChat.taskLabel')}
              task={t('landing.heroChat.task')}
              deadlineLabel={t('landing.heroChat.deadlineLabel')}
              deadline={t('landing.heroChat.deadline')}
            />
          </MotionReveal>
        </div>
      </Container>
    </section>
  )
}
