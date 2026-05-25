import { useEffect, useRef, useState } from 'react'
import { useTranslation } from 'react-i18next'
import { PulseSerialDevice } from '@device/pulse-serial-device.js'
import { MockPulseDevice } from '@device/mock-pulse-device.js'

const TARGET_SAMPLES = 256

// Flip to 'serial' when a real Arduino is wired up. With 'mock', the
// connect/start buttons drive a simulated PPG generator at ~100 Hz so the
// whole UI flow can be exercised on any browser without hardware.
const DEVICE_MODE = 'mock' // 'serial' | 'mock'
const DeviceClass = DEVICE_MODE === 'serial' ? PulseSerialDevice : MockPulseDevice

// Filter all UI-side device logs in DevTools by searching for "[pulse]".
const log = (...args) => console.log('[pulse]', ...args)

// status: 'unsupported' | 'disconnected' | 'connecting' | 'connected'
//       | 'capturing'   | 'done'         | 'error'
export default function PulseWave({ captured, waveform, onCapturedChange }) {
  const { t } = useTranslation()

  const [status, setStatus] = useState(() => {
    if (!DeviceClass.isSupported) return 'unsupported'
    return captured ? 'done' : 'disconnected'
  })
  const [progress, setProgress] = useState(captured ? TARGET_SAMPLES : 0)
  const [errorMsg, setErrorMsg] = useState(null)
  const [displaySamples, setDisplaySamples] = useState(
    Array.isArray(waveform) && waveform.length ? waveform : null
  )

  const deviceRef = useRef(null)
  const samplesRef = useRef([])

  // Cleanup: make sure we don't leave the port open if the component unmounts
  // mid-capture (e.g. step navigation).
  useEffect(() => {
    log('mounted, DEVICE_MODE =', DEVICE_MODE, 'isSupported =', DeviceClass.isSupported)
    return () => {
      log('unmount — disconnecting if needed')
      deviceRef.current?.disconnect().catch(() => {})
      deviceRef.current = null
    }
  }, [])

  const guidance = t('pulse.guidance', { returnObjects: true })

  const ensureDevice = () => {
    if (!deviceRef.current) deviceRef.current = new DeviceClass()
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
    setDisplaySamples(null)
    setStatus('disconnected')
    onCapturedChange(false, null)
  }

  const start = async () => {
    log('start() clicked — target', TARGET_SAMPLES, 'samples')
    setErrorMsg(null)
    samplesRef.current = []
    setProgress(0)
    setDisplaySamples(null)
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
            setDisplaySamples(buf.slice())
            finishCapture(buf.slice())
          } else if (buf.length % 8 === 0) {
            setProgress(buf.length)
            setDisplaySamples(buf.slice())
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
    setDisplaySamples(null)
    setStatus('connected')
  }

  const restart = () => {
    log('restart() clicked')
    samplesRef.current = []
    setProgress(0)
    setDisplaySamples(null)
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

        <Waveform
          filled={status === 'done'}
          samples={displaySamples}
          targetSamples={TARGET_SAMPLES}
        />
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

const VIEW_W = 560
const VIEW_H = 100
const PAD_Y = 8

function buildWaveformPath(samples, targetSamples) {
  if (!samples || samples.length < 2) return null

  // Auto-scale Y to the visible samples so even small swings fill the card.
  let min = Infinity
  let max = -Infinity
  for (const v of samples) {
    if (v < min) min = v
    if (v > max) max = v
  }
  const range = max - min || 1

  // Map index → x across the *target* width so the trace grows left-to-right
  // as samples arrive (rather than rescaling on every new point).
  const denom = Math.max((targetSamples || samples.length) - 1, 1)
  const usableH = VIEW_H - 2 * PAD_Y

  let d = ''
  for (let i = 0; i < samples.length; i++) {
    const x = (i / denom) * VIEW_W
    const y = PAD_Y + usableH - ((samples[i] - min) / range) * usableH
    d += (i === 0 ? 'M' : ' L') + x.toFixed(1) + ' ' + y.toFixed(1)
  }
  return d
}

function Waveform({ filled, samples, targetSamples }) {
  const dataPath = buildWaveformPath(samples, targetSamples)

  // When real samples are present we always disable the CSS "drawing"
  // animation (stroke-dasharray) so the line updates on each sample tick
  // instead of being progressively revealed. When samples are *not* yet
  // present we hide the path entirely — just show the grid — so the user
  // doesn't see a fake animated trace before real data arrives.
  const pathStyle = dataPath
    ? { strokeDasharray: 'none', strokeDashoffset: 0, transition: 'none' }
    : undefined

  return (
    <div className={`waveform ${filled ? 'is-filled' : ''}`}>
      <svg viewBox={`0 0 ${VIEW_W} ${VIEW_H}`} preserveAspectRatio="none">
        <defs>
          <linearGradient id="pulseGrad" x1="0" y1="0" x2="1" y2="0">
            <stop offset="0%" stopColor="#8B1A1A" stopOpacity="0.2" />
            <stop offset="50%" stopColor="#8B1A1A" stopOpacity="1" />
            <stop offset="100%" stopColor="#8B1A1A" stopOpacity="0.2" />
          </linearGradient>
        </defs>
        <g className="waveform-grid">
          {[20, 40, 60, 80].map((y) => (
            <line key={y} x1="0" y1={y} x2={VIEW_W} y2={y} />
          ))}
        </g>
        {dataPath && (
          <path
            className="waveform-path"
            d={dataPath}
            fill="none"
            stroke="url(#pulseGrad)"
            strokeWidth="2"
            style={pathStyle}
          />
        )}
      </svg>
    </div>
  )
}
