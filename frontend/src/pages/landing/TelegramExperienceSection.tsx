import { useTranslation } from 'react-i18next'
import Container from '../../shared/components/Container'
import { ConversationMockup } from '../../shared/components/TelegramMockup'
import MotionReveal from '../../shared/motion/MotionReveal'

export default function TelegramExperienceSection() {
  const { t } = useTranslation()

  const conversations = [
    [t('landing.telegram.conv1.line1'), t('landing.telegram.conv1.line2')],
    [t('landing.telegram.conv2.line1'), t('landing.telegram.conv2.line2'), t('landing.telegram.conv2.line3')],
    [t('landing.telegram.conv3.line1'), t('landing.telegram.conv3.line2')],
  ]

  return (
    <section className="section-divider section-padding bg-surface">
      <Container>
        <MotionReveal className="text-center">
          <h2 className="font-heading text-3xl font-semibold text-white sm:text-4xl">
            {t('landing.telegram.title')}
          </h2>
          <p className="mx-auto mt-5 max-w-xl text-muted">{t('landing.telegram.subtitle')}</p>
        </MotionReveal>

        <div className="mt-16 grid gap-4 md:grid-cols-3">
          {conversations.map((lines, index) => (
            <ConversationMockup key={lines.join('|')} lines={lines} index={index} />
          ))}
        </div>
      </Container>
    </section>
  )
}
