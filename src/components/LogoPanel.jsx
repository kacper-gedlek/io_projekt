import polslLogo from '../polsl-logo.png'

export default function LogoPanel() {
  return (
    <aside className="logo-panel" aria-label="Logo Politechniki Śląskiej">
      <img className="logo-panel__image" src={polslLogo} alt="Politechnika Śląska" />
    </aside>
  )
}
