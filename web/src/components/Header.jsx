import { useTranslation } from 'react-i18next'

export default function Header() {
  const { t, i18n } = useTranslation()

  const toggleLang = () => {
    const next = i18n.language === 'zh' ? 'en' : 'zh'
    i18n.changeLanguage(next)
    localStorage.setItem('lang', next)
  }

  return (
    <header className="site-header">
      <div className="container header-inner">
        <a href="#" className="brand">
          <span className="brand-mark" aria-hidden="true">
            <svg viewBox="0 0 64 64" width="44" height="44">
              <circle cx="32" cy="32" r="30" fill="#8B1A1A" />
              <path
                d="M32 6 a26 26 0 0 1 0 52 a13 13 0 0 1 0 -26 a13 13 0 0 0 0 -26z"
                fill="#F5E6D3"
              />
              <circle cx="32" cy="19" r="4" fill="#8B1A1A" />
              <circle cx="32" cy="45" r="4" fill="#F5E6D3" />
            </svg>
          </span>
          <span className="brand-text">
            <span className="brand-name">{t('brand.name')}</span>
            <span className="brand-sub">{t('brand.subtitle')}</span>
          </span>
        </a>

        <button className="lang-toggle" onClick={toggleLang} aria-label={t('lang.label')}>
          <span className="lang-toggle-char">{t('lang.switch')}</span>
        </button>
      </div>
    </header>
  )
}
