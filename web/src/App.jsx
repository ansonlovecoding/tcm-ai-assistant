import { useEffect, useState } from 'react'
import { useTranslation } from 'react-i18next'
import Header from './components/Header.jsx'
import Footer from './components/Footer.jsx'
import Stepper from './components/Stepper.jsx'
import PatientInfo from './components/steps/PatientInfo.jsx'
import TonguePhoto from './components/steps/TonguePhoto.jsx'
import PulseWave from './components/steps/PulseWave.jsx'
import Diagnose from './components/steps/Diagnose.jsx'

const STEP_KEYS = ['info', 'tongue', 'pulse', 'diagnose']

const initialPatient = { age: '', gender: '', height: '', weight: '' }

export default function App() {
  const { t, i18n } = useTranslation()
  const [stepIndex, setStepIndex] = useState(0)
  const [patient, setPatient] = useState(initialPatient)
  const [tongueImage, setTongueImage] = useState(null) // data URL
  const [pulseCaptured, setPulseCaptured] = useState(false)

  useEffect(() => {
    document.documentElement.lang = i18n.language === 'zh' ? 'zh-CN' : 'en'
    document.documentElement.dataset.lang = i18n.language
  }, [i18n.language])

  const canAdvance = () => {
    if (stepIndex === 0) {
      return patient.age && patient.gender && patient.height && patient.weight
    }
    if (stepIndex === 1) return !!tongueImage
    if (stepIndex === 2) return pulseCaptured
    return true
  }

  const goNext = () => setStepIndex((i) => Math.min(i + 1, STEP_KEYS.length - 1))
  const goPrev = () => setStepIndex((i) => Math.max(i - 1, 0))

  const restart = () => {
    setPatient(initialPatient)
    setTongueImage(null)
    setPulseCaptured(false)
    setStepIndex(0)
  }

  const renderStep = () => {
    switch (STEP_KEYS[stepIndex]) {
      case 'info':
        return <PatientInfo value={patient} onChange={setPatient} />
      case 'tongue':
        return <TonguePhoto image={tongueImage} onChange={setTongueImage} />
      case 'pulse':
        return <PulseWave captured={pulseCaptured} onCapturedChange={setPulseCaptured} />
      case 'diagnose':
        return (
          <Diagnose
            patient={patient}
            tongueImage={tongueImage}
            pulseCaptured={pulseCaptured}
            onRestart={restart}
          />
        )
      default:
        return null
    }
  }

  const stepKey = STEP_KEYS[stepIndex]
  const isLast = stepIndex === STEP_KEYS.length - 1

  return (
    <div className="app">
      <div className="paper-texture" aria-hidden="true" />
      <Header />
      <main>
        <section className="intro">
          <div className="container">
            <div className="seal seal-center">
              <span>{t('intro.seal')}</span>
            </div>
            <h1 className="intro-title">{t('intro.title')}</h1>
            <p className="intro-desc">{t('intro.desc')}</p>
          </div>
        </section>

        <section className="flow">
          <div className="container">
            <Stepper steps={STEP_KEYS} current={stepIndex} />

            <div className="step-panel">
              <div className="step-heading">
                <div className="ornament" aria-hidden="true">❖</div>
                <h2>{t(`steps.${stepKey}.title`)}</h2>
                <p>{t(`steps.${stepKey}.desc`)}</p>
              </div>

              <div className="step-body">{renderStep()}</div>

              {!isLast && (
                <div className="step-nav">
                  <button
                    className="btn btn-ghost"
                    onClick={goPrev}
                    disabled={stepIndex === 0}
                  >
                    {t('nav_btn.prev')}
                  </button>
                  <button
                    className="btn btn-primary"
                    onClick={goNext}
                    disabled={!canAdvance()}
                  >
                    {t('nav_btn.next')}
                  </button>
                </div>
              )}
              {isLast && (
                <div className="step-nav">
                  <button className="btn btn-ghost" onClick={goPrev}>
                    {t('nav_btn.prev')}
                  </button>
                </div>
              )}
            </div>
          </div>
        </section>
      </main>
      <Footer />
    </div>
  )
}
