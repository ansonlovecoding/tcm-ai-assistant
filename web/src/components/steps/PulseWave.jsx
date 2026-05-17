import { useEffect, useRef, useState } from 'react'
import { useTranslation } from 'react-i18next'

// 'disconnected' | 'connecting' | 'connected' | 'capturing' | 'done'
export default function PulseWave({ captured, onCapturedChange }) {
  const { t } = useTranslation()
  const [status, setStatus] = useState(captured ? 'done' : 'disconnected')
  const timerRef = useRef(null)
  const guidance = t('pulse.guidance', { returnObjects: true })

  useEffect(() => () => clearTimeout(timerRef.current), [])

  const connect = () => {
    setStatus('connecting')
    timerRef.current = setTimeout(() => setStatus('connected'), 900)
  }

  const disconnect = () => {
    clearTimeout(timerRef.current)
    setStatus('disconnected')
    onCapturedChange(false)
  }

  const start = () => {
    setStatus('capturing')
    timerRef.current = setTimeout(() => {
      setStatus('done')
      onCapturedChange(true)
    }, 3200)
  }

  const stop = () => {
    clearTimeout(timerRef.current)
    setStatus('connected')
  }

  const restart = () => {
    onCapturedChange(false)
    setStatus('connected')
  }

  const statusKey = `pulse.device_status_${status}`

  return (
    <div className="pulse-step">
      <div className="instruction-card">
        <h3 className="instruction-title">{t('pulse.guidance_title')}</h3>
        <ol className="instruction-list">
          {Array.isArray(guidance) &&
            guidance.map((g, i) => (
              <li key={i}>
                <span className="instruction-num">{i + 1}</span>
                <span>{g}</span>
              </li>
            ))}
        </ol>
      </div>

      <div className="device-card">
        <div className="device-head">
          <h3 className="instruction-title">{t('pulse.device_title')}</h3>
          <span className={`device-status status-${status}`}>
            <span className="status-dot" /> {t(statusKey)}
          </span>
        </div>

        <Waveform animated={status === 'capturing'} filled={status === 'done'} />
        <p className="waveform-caption">{t('pulse.waveform_label')}</p>

        <div className="device-actions">
          {status === 'disconnected' && (
            <button className="btn btn-primary" onClick={connect}>
              {t('pulse.connect')}
            </button>
          )}
          {status === 'connecting' && (
            <button className="btn btn-primary" disabled>
              {t('pulse.device_status_connecting')}
            </button>
          )}
          {status === 'connected' && (
            <>
              <button className="btn btn-primary" onClick={start}>
                {t('pulse.start')}
              </button>
              <button className="btn btn-ghost" onClick={disconnect}>
                {t('pulse.disconnect')}
              </button>
            </>
          )}
          {status === 'capturing' && (
            <button className="btn btn-ghost" onClick={stop}>
              {t('pulse.stop')}
            </button>
          )}
          {status === 'done' && (
            <button className="btn btn-ghost" onClick={restart}>
              {t('pulse.restart')}
            </button>
          )}
        </div>
      </div>
    </div>
  )
}

function Waveform({ animated, filled }) {
  // Stylized pulse: small upstroke, sharp main peak, dicrotic notch, decay
  const path =
    'M0 60 L40 60 L60 30 L72 70 L88 22 L100 78 L120 50 L150 58 L170 60 L210 60 L230 28 L242 72 L258 22 L270 78 L290 52 L320 58 L340 60 L380 60 L400 30 L412 70 L428 22 L440 78 L460 50 L490 58 L510 60 L560 60'

  return (
    <div className={`waveform ${animated ? 'is-animated' : ''} ${filled ? 'is-filled' : ''}`}>
      <svg viewBox="0 0 560 100" preserveAspectRatio="none">
        <defs>
          <linearGradient id="pulseGrad" x1="0" y1="0" x2="1" y2="0">
            <stop offset="0%" stopColor="#8B1A1A" stopOpacity="0.2" />
            <stop offset="50%" stopColor="#8B1A1A" stopOpacity="1" />
            <stop offset="100%" stopColor="#8B1A1A" stopOpacity="0.2" />
          </linearGradient>
        </defs>
        {/* grid */}
        <g className="waveform-grid">
          {[20, 40, 60, 80].map((y) => (
            <line key={y} x1="0" y1={y} x2="560" y2={y} />
          ))}
        </g>
        <path className="waveform-path" d={path} fill="none" stroke="url(#pulseGrad)" strokeWidth="2" />
      </svg>
    </div>
  )
}
