import { useTranslation } from 'react-i18next'

const GENDERS = ['male', 'female', 'other']

export default function PatientInfo({ value, onChange }) {
  const { t } = useTranslation()

  const update = (field) => (e) => {
    onChange({ ...value, [field]: e.target.value })
  }

  const setGender = (g) => onChange({ ...value, gender: g })

  return (
    <div className="patient-form">
      <div className="form-row">
        <label className="form-field">
          <span className="form-label">{t('form.age')}</span>
          <div className="input-with-unit">
            <input
              type="number"
              min="0"
              max="150"
              value={value.age}
              onChange={update('age')}
              placeholder={t('form.age_placeholder')}
            />
            <span className="input-unit">{t('form.age_unit')}</span>
          </div>
        </label>

        <div className="form-field">
          <span className="form-label">{t('form.gender')}</span>
          <div className="chip-group" role="radiogroup">
            {GENDERS.map((g) => (
              <button
                key={g}
                type="button"
                role="radio"
                aria-checked={value.gender === g}
                className={`chip ${value.gender === g ? 'is-active' : ''}`}
                onClick={() => setGender(g)}
              >
                {t(`form.gender_${g}`)}
              </button>
            ))}
          </div>
        </div>
      </div>

      <div className="form-row">
        <label className="form-field">
          <span className="form-label">{t('form.height')}</span>
          <div className="input-with-unit">
            <input
              type="number"
              min="30"
              max="260"
              value={value.height}
              onChange={update('height')}
              placeholder={t('form.height_placeholder')}
            />
            <span className="input-unit">{t('form.height_unit')}</span>
          </div>
        </label>

        <label className="form-field">
          <span className="form-label">{t('form.weight')}</span>
          <div className="input-with-unit">
            <input
              type="number"
              min="2"
              max="400"
              value={value.weight}
              onChange={update('weight')}
              placeholder={t('form.weight_placeholder')}
            />
            <span className="input-unit">{t('form.weight_unit')}</span>
          </div>
        </label>
      </div>
    </div>
  )
}
