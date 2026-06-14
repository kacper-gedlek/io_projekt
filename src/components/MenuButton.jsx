export default function MenuButton({ onOpen }) {
  return (
    <button className="menu-btn" type="button" onClick={onOpen} aria-haspopup="dialog">
      <span className="menu-btn__icon" aria-hidden="true" />
      <span className="menu-btn__label">Menu</span>
    </button>
  )
}
