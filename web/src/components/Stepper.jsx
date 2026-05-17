import { useTranslation } from 'react-i18next'

export default function Stepper({ steps, current }) {
  const { t } = useTranslation()

  return (
    <div className="stepper" aria-label="progress">
      <ol className="stepper-track">
        {steps.map((key, i) => {
          const state =
            i < current ? 'done' : i === current ? 'active' : 'pending'
          return (
            <li key={key} className={`stepper-item is-${state}`}>
              <span className="stepper-circle" aria-hidden="true">
                {i < current ? '✓' : i + 1}
              </span>
              <span className="stepper-label">{t(`steps.${key}.label`)}</span>
              {i < steps.length - 1 && (
                <span className="stepper-line" aria-hidden="true" />
              )}
            </li>
          )
        })}
      </ol>
      <p className="stepper-count">
        {t('stepper.step')} {current + 1} {t('stepper.of')} {steps.length}{' '}
        {t('stepper.step_unit')}
      </p>
    </div>
  )
}
