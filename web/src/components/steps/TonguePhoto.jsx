import { useEffect, useMemo, useRef, useState } from 'react'
import { useTranslation } from 'react-i18next'

export default function TonguePhoto({ file, onChange }) {
  const { t } = useTranslation()
  const inputRef = useRef(null)
  const [dragging, setDragging] = useState(false)

  const tips = t('tongue.tips', { returnObjects: true })

  const previewUrl = useMemo(() => (file ? URL.createObjectURL(file) : null), [file])
  useEffect(() => {
    return () => {
      if (previewUrl) URL.revokeObjectURL(previewUrl)
    }
  }, [previewUrl])

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

        {previewUrl && (
          <div className="preview">
            <img src={previewUrl} alt={t('tongue.preview_alt')} />
            <button
              type="button"
              className="btn btn-ghost"
              onClick={() => inputRef.current?.click()}
            >
              {t('tongue.change')}
            </button>
          </div>
        )}

        <input
          ref={inputRef}
          type="file"
          accept="image/*"
          capture="environment"
          hidden
          onChange={onSelect}
        />
      </div>
    </div>
  )
}
