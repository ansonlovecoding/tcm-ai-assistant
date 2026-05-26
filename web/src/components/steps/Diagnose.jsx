import { useEffect, useState } from 'react'
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

// `food_recommendations` / `foods_to_avoid` come back as
// `{zh: [...], en: [...]}` (arrays per language, not single strings).
function pickFoodList(bi, lang) {
  if (!bi) return []
  const list = bi[lang] ?? bi.zh ?? bi.en ?? []
  return Array.isArray(list) ? list : []
}

// Static SVG shown while a chip is fetching its Pexels photo, and as the
// fallback when no photo is found (or the API isn't configured).
const FOOD_PLACEHOLDER = '/foods/_placeholder.svg'

// In-memory cache of Pexels lookups, keyed by lowercase English food name.
// Pending lookups store the Promise so concurrent chips for the same food
// only trigger one network round-trip; resolved entries store the URL (or
// `null` for "no photo found" so we don't retry forever).
const _foodImageCache = new Map()

function fetchFoodImage(query) {
  const key = String(query || '').trim().toLowerCase()
  if (!key) return Promise.resolve(null)
  if (_foodImageCache.has(key)) return Promise.resolve(_foodImageCache.get(key))

  const p = api.foodImage(key)
    .then((r) => r?.url ?? null)
    .catch(() => null)
    .then((url) => {
      // Replace the Promise entry with the resolved value so subsequent
      // callers get the URL synchronously.
      _foodImageCache.set(key, url)
      return url
    })
  _foodImageCache.set(key, p)
  return p
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
  // null while no chip is being previewed; { label, src } when the lightbox
  // is open. Closing the lightbox returns it to null.
  const [preview, setPreview] = useState(null)

  // Close the preview on Escape. Also lock body scroll while it's open so
  // the page underneath doesn't drift around when the overlay appears.
  useEffect(() => {
    if (!preview) return
    const onKey = (e) => { if (e.key === 'Escape') setPreview(null) }
    window.addEventListener('keydown', onKey)
    const prevOverflow = document.body.style.overflow
    document.body.style.overflow = 'hidden'
    return () => {
      window.removeEventListener('keydown', onKey)
      document.body.style.overflow = prevOverflow
    }
  }, [preview])

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

      {phase === 'done' && result && (() => {
        // Display labels follow the active locale; Pexels lookups always use
        // the English name (parallel index in the `en` array) because the API
        // returns much better matches for "Chinese yam" than for "山药".
        const recLabels = pickFoodList(result.food_recommendations, lang)
        const recQueries = result.food_recommendations?.en ?? recLabels
        const avoidLabels = pickFoodList(result.foods_to_avoid, lang)
        const avoidQueries = result.foods_to_avoid?.en ?? avoidLabels
        return (
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

            {recLabels.length > 0 && (
              <div className="result-block">
                <span className="result-label">{t('diagnose.result_foods_recommended')}</span>
                <ul className="food-chips">
                  {recLabels.map((label, i) => (
                    <FoodChip
                      key={`rec-${i}`}
                      label={label}
                      query={recQueries[i] || label}
                      variant="good"
                      onPreview={setPreview}
                    />
                  ))}
                </ul>
              </div>
            )}

            {avoidLabels.length > 0 && (
              <div className="result-block">
                <span className="result-label">{t('diagnose.result_foods_avoid')}</span>
                <ul className="food-chips">
                  {avoidLabels.map((label, i) => (
                    <FoodChip
                      key={`avoid-${i}`}
                      label={label}
                      query={avoidQueries[i] || label}
                      variant="bad"
                      onPreview={setPreview}
                    />
                  ))}
                </ul>
              </div>
            )}

            <p className="result-disclaimer">{pickLang(result.disclaimer, lang)}</p>
            <button className="btn btn-ghost" onClick={onRestart}>
              {t('diagnose.restart')}
            </button>
          </div>
        )
      })()}

      {preview && (
        <div
          className="food-preview-backdrop"
          role="dialog"
          aria-modal="true"
          aria-label={preview.label}
          onClick={() => setPreview(null)}
        >
          <figure className="food-preview" onClick={(e) => e.stopPropagation()}>
            <button
              type="button"
              className="food-preview-close"
              aria-label={t('diagnose.preview_close')}
              onClick={() => setPreview(null)}
            >×</button>
            <img className="food-preview-img" src={preview.src} alt={preview.label} />
            <figcaption className="food-preview-caption">{preview.label}</figcaption>
          </figure>
        </div>
      )}
    </div>
  )
}

// Single food chip — Pexels photo + label.
//
// `label` is what we show next to the image (in the active UI locale).
// `query` is the search term we send to /api/foods/image — always English
// because Pexels returns much richer results for "Chinese yam" than for
// "山药". Both come pre-paired from the parallel zh/en arrays.
// `onPreview({label, src})` fires when the user clicks a chip that has a
// real photo (not the placeholder), so the parent can open the lightbox.
//
// The img starts on the placeholder SVG, swaps to the fetched URL when the
// lookup resolves, and falls back to the placeholder again if either the
// fetch or the image load itself fails.
function FoodChip({ label, query, variant, onPreview }) {
  const [src, setSrc] = useState(FOOD_PLACEHOLDER)

  useEffect(() => {
    let alive = true
    fetchFoodImage(query).then((url) => {
      if (alive && url) setSrc(url)
    })
    return () => { alive = false }
  }, [query])

  const handleError = (e) => {
    if (e.currentTarget.src !== FOOD_PLACEHOLDER) {
      e.currentTarget.src = FOOD_PLACEHOLDER
    }
  }

  const hasRealPhoto = src !== FOOD_PLACEHOLDER
  const handleClick = () => {
    if (hasRealPhoto) onPreview?.({ label, src })
  }

  return (
    <li>
      <button
        type="button"
        className={`food-chip food-chip-${variant}`}
        onClick={handleClick}
        disabled={!hasRealPhoto}
        title={hasRealPhoto ? label : ''}
      >
        <img
          className="food-chip-img"
          src={src}
          alt={label}
          loading="lazy"
          onError={handleError}
        />
        <span className="food-chip-label">{label}</span>
      </button>
    </li>
  )
}
