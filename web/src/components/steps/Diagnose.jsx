import { useState } from 'react'
import { useTranslation } from 'react-i18next'

export default function Diagnose({ patient, tongueImage, pulseCaptured, onRestart }) {
  const { t } = useTranslation()
  const [phase, setPhase] = useState('idle') // 'idle' | 'analyzing' | 'done'

  const start = () => {
    setPhase('analyzing')
    setTimeout(() => setPhase('done'), 2400)
  }

  const summary = [
    { label: t('diagnose.field_age'), value: patient.age ? `${patient.age} ${t('form.age_unit')}` : t('diagnose.value_missing') },
    { label: t('diagnose.field_gender'), value: patient.gender ? t(`form.gender_${patient.gender}`) : t('diagnose.value_missing') },
    { label: t('diagnose.field_height'), value: patient.height ? `${patient.height} ${t('form.height_unit')}` : t('diagnose.value_missing') },
    { label: t('diagnose.field_weight'), value: patient.weight ? `${patient.weight} ${t('form.weight_unit')}` : t('diagnose.value_missing') },
    { label: t('diagnose.field_tongue'), value: tongueImage ? t('diagnose.value_uploaded') : t('diagnose.value_missing') },
    { label: t('diagnose.field_pulse'), value: pulseCaptured ? t('diagnose.value_captured') : t('diagnose.value_missing') }
  ]

  return (
    <div className="diagnose-step">
      <div className="summary-card">
        <h3 className="instruction-title">{t('diagnose.summary_title')}</h3>
        <dl className="summary-grid">
          {summary.map((row) => (
            <div className="summary-row" key={row.label}>
              <dt>{row.label}</dt>
              <dd>{row.value}</dd>
            </div>
          ))}
        </dl>
      </div>

      {phase === 'idle' && (
        <div className="diagnose-action">
          <button className="btn btn-primary btn-lg" onClick={start}>
            {t('diagnose.start')}
          </button>
        </div>
      )}

      {phase === 'analyzing' && (
        <div className="analyzing">
          <div className="analyzing-spinner" aria-hidden="true">
            <span />
            <span />
            <span />
          </div>
          <p>{t('diagnose.analyzing')}</p>
        </div>
      )}

      {phase === 'done' && (
        <div className="result-card">
          <div className="ornament" aria-hidden="true">❖</div>
          <h3>{t('diagnose.result_title')}</h3>
          <div className="result-block">
            <span className="result-label">{t('diagnose.result_pattern')}</span>
            <p className="result-value">{t('diagnose.result_pattern_value')}</p>
          </div>
          <div className="result-block">
            <span className="result-label">{t('diagnose.result_advice')}</span>
            <p className="result-value">{t('diagnose.result_advice_value')}</p>
          </div>
          <p className="result-disclaimer">{t('diagnose.disclaimer')}</p>
          <button className="btn btn-ghost" onClick={onRestart}>
            {t('diagnose.restart')}
          </button>
        </div>
      )}
    </div>
  )
}
