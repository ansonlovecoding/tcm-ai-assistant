import { useEffect, useRef, useState } from 'react'
import { useTranslation } from 'react-i18next'
import { PulseSerialDevice } from '@device/pulse-serial-device.js'

const TARGET_SAMPLES = 256

// Filter all UI-side device logs in DevTools by searching for "[pulse]".
const log = (...args) => console.log('[pulse]', ...args)

// status: 'unsupported' | 'disconnected' | 'connecting' | 'connected'
//       | 'capturing'   | 'done'         | 'error'
export default function PulseWave({ captured, waveform, onCapturedChange }) {
  const { t } = useTranslation()

  const [status, setStatus] = useState(() => {
    if (!PulseSerialDevice.isSupported) return 'unsupported'
    return captured ? 'done' : 'disconnected'
  })
  const [progress, setProgress] = useState(captured ? TARGET_SAMPLES : 0)
  const [errorMsg, setErrorMsg] = useState(null)

  const deviceRef = useRef(null)
  const samplesRef = useRef([])

  // Cleanup: make sure we don't leave the port open if the component unmounts
  // mid-capture (e.g. step navigation).
  useEffect(() => {
    log('mounted, isSupported =', PulseSerialDevice.isSupported)
    return () => {
      log('unmount — disconnecting if needed')
      deviceRef.current?.disconnect().catch(() => {})
      deviceRef.current = null
    }
  }, [])

  const guidance = t('pulse.guidance', { returnObjects: true })

  const ensureDevice = () => {
    if (!deviceRef.current) deviceRef.current = new PulseSerialDevice()
    return deviceRef.current
  }

  const connect = async () => {
    log('connect() clicked')
    setErrorMsg(null)
    setStatus('connecting')
    try {
      await ensureDevice().connect()
      log('connect() -> connected')
      setStatus('connected')
    } catch (e) {
      // User-cancelled chooser is a NotFoundError; treat as a soft reset.
      if (e?.name === 'NotFoundError') {
        log('port chooser dismissed by user')
      } else {
        log('connect() failed:', e?.message || e)
        setErrorMsg(e.message || String(e))
      }
      setStatus('disconnected')
    }
  }

  const disconnect = async () => {
    log('disconnect() clicked')
    await deviceRef.current?.disconnect().catch(() => {})
    deviceRef.current = null
    samplesRef.current = []
    setProgress(0)
    setStatus('disconnected')
    onCapturedChange(false, null)
  }

  const start = async () => {
    log('start() clicked — target', TARGET_SAMPLES, 'samples')
    setErrorMsg(null)
    samplesRef.current = []
    setProgress(0)
    setStatus('capturing')

    try {
      await ensureDevice().startCapture({
        onSample: (value) => {
          const buf = samplesRef.current
          if (buf.length >= TARGET_SAMPLES) return
          buf.push(value)
          // Throttle re-renders: only paint every 8 samples and on completion.
          if (buf.length === TARGET_SAMPLES) {
            setProgress(TARGET_SAMPLES)
            finishCapture(buf.slice())
          } else if (buf.length % 8 === 0) {
            setProgress(buf.length)
          }
        },
        onError: (e) => {
          log('capture stream error:', e?.message || e)
          setErrorMsg(e.message || String(e))
        }
      })
    } catch (e) {
      log('start() failed:', e?.message || e)
      setStatus('error')
      setErrorMsg(e.message || String(e))
    }
  }

  const finishCapture = async (waveformOut) => {
    await deviceRef.current?.stopCapture().catch(() => {})
    const min = Math.min(...waveformOut)
    const max = Math.max(...waveformOut)
    const mean = waveformOut.reduce((a, b) => a + b, 0) / waveformOut.length
    log(
      `capture complete — ${waveformOut.length} samples, min=${min} max=${max} mean=${mean.toFixed(1)}`,
      'first 5:', waveformOut.slice(0, 5),
      'last 5:', waveformOut.slice(-5)
    )
    setStatus('done')
    onCapturedChange(true, waveformOut)
  }

  const stop = async () => {
    log('stop() clicked at', samplesRef.current.length, '/', TARGET_SAMPLES, 'samples')
    await deviceRef.current?.stopCapture().catch(() => {})
    samplesRef.current = []
    setProgress(0)
    setStatus('connected')
  }

  const restart = () => {
    log('restart() clicked')
    samplesRef.current = []
    setProgress(0)
    setStatus('connected')
    onCapturedChange(false, null)
  }

  const statusKey = `pulse.device_status_${status}`
  const showProgress = status === 'capturing' || status === 'done'

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
        <p className="waveform-caption">
          {showProgress
            ? t('pulse.capture_progress', { current: progress, total: TARGET_SAMPLES })
            : t('pulse.waveform_label')}
        </p>

        {errorMsg && <p className="step-error">⚠ {errorMsg}</p>}

        <div className="device-actions">
          {status === 'unsupported' && (
            <p className="step-error">⚠ {t('pulse.unsupported')}</p>
          )}
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
            <>
              <button className="btn btn-ghost" onClick={restart}>
                {t('pulse.restart')}
              </button>
              <button className="btn btn-ghost" onClick={disconnect}>
                {t('pulse.disconnect')}
              </button>
            </>
          )}
          {status === 'error' && (
            <button className="btn btn-primary" onClick={disconnect}>
              {t('pulse.disconnect')}
            </button>
          )}
        </div>
      </div>
    </div>
  )
}

function Waveform({ animated, filled }) {
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
