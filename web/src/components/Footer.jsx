import { useTranslation } from 'react-i18next'

export default function Footer() {
  const { t } = useTranslation()

  return (
    <footer className="site-footer">
      <div className="container footer-inner">
        <span>{t('footer.rights')}</span>
        <a href="mailto:contact@tcm.ai">{t('footer.contact')}</a>
      </div>
    </footer>
  )
}
