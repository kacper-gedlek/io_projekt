export default function CommunicationBox({ message }) {
  return (
    <aside className="communication-box" aria-label="Komunikat">
      <div className="communication-header">
        <span className="communication-header__dot" />
        <span>Komunikat</span>
      </div>
      <p className="communication-box__text">{message}</p>
    </aside>
  )
}
