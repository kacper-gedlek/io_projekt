export default function MenuButton({ onOpen }) {
  return (
    <button className="menu-btn menu-btn--start" type="button" onClick={onOpen} aria-haspopup="dialog">
      <span className="menu-btn__label">Start</span>
    </button>
  )
}