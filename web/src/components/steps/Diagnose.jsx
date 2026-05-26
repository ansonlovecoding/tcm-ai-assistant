import { useState } from 'react'
import { useTranslation } from 'react-i18next'
import { api, pickLang } from '../../api.js'

// One-line summary for the review screen: list every distinct detected
// label with its count, e.g. "白苔舌×1, 裂纹舌×1, 齿痕舌×2".
function formatTongueSummary(analysis, lang) {
  const labels = analysis?.detected_labels
  if (!Array.isArray(labels) || labels.length === 0) return ''
  return labels
    .map((l) => `${pickLang(l.name, lang)}${l.count > 1 ? `×${l.count}` : ''}`)
    .join(', ')
}

export default function Diagnose({
  sessionId,
  patient,
  tongueFile,
  tongueAnalysis,
  pulseCaptured,
  pulseAnalysis,
  onRestart
}) {
  const { t, i18n } = useTranslation()
  const lang = i18n.language
  const [phase, setPhase] = useState('idle') // 'idle' | 'analyzing' | 'done' | 'error'
  const [result, setResult] = useState(null)
  const [error, setError] = useState(null)

  const start = async () => {
    if (!sessionId) {
      setError('missing session')
      setPhase('error')
      return
    }
    setPhase('analyzing')
    setError(null)
    try {
      const r = await api.diagnose(sessionId)
      setResult(r)
      setPhase('done')
    } catch (e) {
      setError(e.message || String(e))
      setPhase('error')
    }
  }

  const summary = [
    {
      label: t('diagnose.field_age'),
      value: patient.age ? `${patient.age} ${t('form.age_unit')}` : t('diagnose.value_missing')
    },
    {
      label: t('diagnose.field_gender'),
      value: patient.gender ? t(`form.gender_${patient.gender}`) : t('diagnose.value_missing')
    },
    {
      label: t('diagnose.field_height'),
      value: patient.height ? `${patient.height} ${t('form.height_unit')}` : t('diagnose.value_missing')
    },
    {
      label: t('diagnose.field_weight'),
      value: patient.weight ? `${patient.weight} ${t('form.weight_unit')}` : t('diagnose.value_missing')
    },
    {
      label: t('diagnose.field_tongue'),
      value: tongueAnalysis
        ? formatTongueSummary(tongueAnalysis, lang) || t('diagnose.value_uploaded')
        : tongueFile
          ? t('diagnose.value_uploaded')
          : t('diagnose.value_missing')
    },
    {
      label: t('diagnose.field_pulse'),
      value: pulseAnalysis
        ? `SBP: ${pulseAnalysis.sbp.toFixed(2)} mmHg, DBP: ${pulseAnalysis.dbp.toFixed(2)} mmHg`
        : pulseCaptured
          ? t('diagnose.value_captured')
          : t('diagnose.value_missing')
    }
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
          <button className="btn btn-primary btn-lg" onClick={start} disabled={!sessionId}>
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

      {phase === 'error' && (
        <div className="analyzing">
          <p className="step-error">⚠ {error}</p>
          <button className="btn btn-ghost" onClick={start}>
            {t('diagnose.start')}
          </button>
        </div>
      )}

      {phase === 'done' && result && (
        <div className="result-card">
          <div className="ornament" aria-hidden="true">❖</div>
          <h3>{t('diagnose.result_title')}</h3>

          <div className="result-block">
            <span className="result-label">{t('diagnose.result_pattern')}</span>
            <p className="result-value">{pickLang(result.pattern, lang)}</p>
            <p className="result-value result-summary">{pickLang(result.summary, lang)}</p>
          </div>

          <div className="result-block">
            <span className="result-label">{t('diagnose.result_advice')}</span>
            <p className="result-value">{pickLang(result.advice.lifestyle, lang)}</p>
            <p className="result-value">{pickLang(result.advice.diet, lang)}</p>
            <p className="result-value">{pickLang(result.advice.herbal_tea, lang)}</p>
          </div>

          <p className="result-disclaimer">{pickLang(result.disclaimer, lang)}</p>
          <button className="btn btn-ghost" onClick={onRestart}>
            {t('diagnose.restart')}
          </button>
        </div>
      )}
    </div>
  )
}
