import { useEffect, useMemo, useRef, useState } from 'react'
import { useTranslation } from 'react-i18next'

// Center-zoom applied to the live preview (via CSS scale) AND to the captured
// frame (via canvas crop), so the saved image matches what the user framed.
const CAMERA_ZOOM = 5.5

export default function TonguePhoto({ file, onChange }) {
  const { t } = useTranslation()
  const inputRef = useRef(null)
  const videoRef = useRef(null)
  const streamRef = useRef(null)
  const [dragging, setDragging] = useState(false)
  const [mode, setMode] = useState('upload') // 'upload' | 'camera'
  const [cameraError, setCameraError] = useState(null)
  const [cameraReady, setCameraReady] = useState(false)

  const tips = t('tongue.tips', { returnObjects: true })

  const previewUrl = useMemo(() => (file ? URL.createObjectURL(file) : null), [file])
  useEffect(() => {
    return () => {
      if (previewUrl) URL.revokeObjectURL(previewUrl)
    }
  }, [previewUrl])

  const stopStream = () => {
    const s = streamRef.current
    if (s) {
      s.getTracks().forEach((tr) => tr.stop())
      streamRef.current = null
    }
    if (videoRef.current) videoRef.current.srcObject = null
    setCameraReady(false)
  }

  // Always release the camera on unmount, otherwise the indicator stays on.
  useEffect(() => () => stopStream(), [])

  // Release the camera when the user leaves camera mode or once a file exists.
  useEffect(() => {
    if (mode !== 'camera' || file) stopStream()
  }, [mode, file])

  const startCamera = async () => {
    setCameraError(null)
    if (!navigator.mediaDevices?.getUserMedia) {
      setCameraError(t('tongue.camera_unsupported'))
      return
    }
    try {
      const stream = await navigator.mediaDevices.getUserMedia({
        video: { facingMode: 'environment' },
        audio: false
      })
      streamRef.current = stream
      if (videoRef.current) {
        videoRef.current.srcObject = stream
        await videoRef.current.play().catch(() => {})
      }
      setCameraReady(true)
    } catch (e) {
      setCameraError(e?.message || String(e))
      stopStream()
    }
  }

  const capture = () => {
    const video = videoRef.current
    if (!video || !streamRef.current) return
    const w = video.videoWidth
    const h = video.videoHeight
    if (!w || !h) return
    // Crop the centered region that the CSS scale shows on screen.
    const sw = w / CAMERA_ZOOM
    const sh = h / CAMERA_ZOOM
    const sx = (w - sw) / 2
    const sy = (h - sh) / 2
    const canvas = document.createElement('canvas')
    canvas.width = sw
    canvas.height = sh
    canvas.getContext('2d').drawImage(video, sx, sy, sw, sh, 0, 0, sw, sh)
    canvas.toBlob(
      (blob) => {
        if (!blob) return
        const f = new File([blob], `tongue-${Date.now()}.jpg`, { type: 'image/jpeg' })
        onChange(f)
        stopStream()
      },
      'image/jpeg',
      0.92
    )
  }

  const handleFile = (f) => {
    if (!f || !f.type.startsWith('image/')) return
    onChange(f)
  }

  const onSelect = (e) => handleFile(e.target.files?.[0])
  const onDrop = (e) => {
    e.preventDefault()
    setDragging(false)
    handleFile(e.dataTransfer.files?.[0])
  }

  const clearImage = () => {
    onChange(null)
    setCameraError(null)
  }

  return (
    <div className="tongue-step">
      <div className="instruction-card">
        <h3 className="instruction-title">{t('tongue.instructions_title')}</h3>
        <ol className="instruction-list">
          {Array.isArray(tips) &&
            tips.map((tip, i) => (
              <li key={i}>
                <span className="instruction-num">{i + 1}</span>
                <span>{tip}</span>
              </li>
            ))}
        </ol>
      </div>

      <div className="upload-card">
        <h3 className="instruction-title">{t('tongue.upload_title')}</h3>

        {!previewUrl && (
          <div className="upload-mode-toggle" role="tablist">
            <button
              type="button"
              role="tab"
              aria-selected={mode === 'upload'}
              className={`chip ${mode === 'upload' ? 'is-active' : ''}`}
              onClick={() => setMode('upload')}
            >
              {t('tongue.mode_upload')}
            </button>
            <button
              type="button"
              role="tab"
              aria-selected={mode === 'camera'}
              className={`chip ${mode === 'camera' ? 'is-active' : ''}`}
              onClick={() => setMode('camera')}
            >
              {t('tongue.mode_camera')}
            </button>
          </div>
        )}

        {!previewUrl && mode === 'upload' && (
          <div
            className={`dropzone ${dragging ? 'is-dragging' : ''}`}
            onClick={() => inputRef.current?.click()}
            onDragOver={(e) => {
              e.preventDefault()
              setDragging(true)
            }}
            onDragLeave={() => setDragging(false)}
            onDrop={onDrop}
            role="button"
            tabIndex={0}
          >
            <svg viewBox="0 0 64 64" className="dropzone-icon" aria-hidden="true">
              <path
                d="M14 44 V20 a2 2 0 0 1 2-2 h32 a2 2 0 0 1 2 2 v24"
                stroke="currentColor"
                strokeWidth="2"
                fill="none"
              />
              <path d="M14 44 l10-10 8 8 8-12 14 14" stroke="currentColor" strokeWidth="2" fill="none" />
              <circle cx="40" cy="26" r="3" fill="currentColor" />
              <path d="M32 50 v-12 m-6 6 l6-6 6 6" stroke="currentColor" strokeWidth="2" fill="none" />
            </svg>
            <p className="dropzone-hint">{t('tongue.upload_hint')}</p>
          </div>
        )}

        {!previewUrl && mode === 'camera' && (
          <div className="camera">
            <div className="camera-frame">
              <video
                ref={videoRef}
                className={cameraReady ? 'is-ready' : ''}
                playsInline
                muted
                aria-label={t('tongue.preview_alt')}
                style={cameraReady ? { transform: `scale(${CAMERA_ZOOM})`, transformOrigin: 'center center' } : undefined}
              />
              {!cameraReady && (
                <p className="camera-placeholder">
                  {cameraError ? `⚠ ${cameraError}` : t('tongue.camera_idle')}
                </p>
              )}
            </div>
            <div className="camera-actions">
              {!cameraReady ? (
                <button type="button" className="btn btn-primary" onClick={startCamera}>
                  {t('tongue.camera_start')}
                </button>
              ) : (
                <>
                  <button type="button" className="btn btn-primary" onClick={capture}>
                    {t('tongue.camera_capture')}
                  </button>
                  <button type="button" className="btn btn-ghost" onClick={stopStream}>
                    {t('tongue.camera_stop')}
                  </button>
                </>
              )}
            </div>
          </div>
        )}

        {previewUrl && (
          <div className="preview">
            <img src={previewUrl} alt={t('tongue.preview_alt')} />
            <button type="button" className="btn btn-ghost" onClick={clearImage}>
              {t('tongue.change')}
            </button>
          </div>
        )}

        <input
          ref={inputRef}
          type="file"
          accept="image/*"
          hidden
          onChange={onSelect}
        />
      </div>
    </div>
  )
}
