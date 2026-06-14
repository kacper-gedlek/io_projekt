export default function RoleMenu({ selected, onSelect, open, onClose }) {
  if (!open) return null

  const pickRole = (role) => {
    onSelect(role)
    onClose()
  }

  return (
    <div className="menu-overlay" role="dialog" aria-modal="true" aria-label="Wybór widoku">
      <div className="role-menu">
        <button className="close-btn" type="button" onClick={onClose} aria-label="Zamknij menu">×</button>
        <p className="menu-eyebrow">Wybierz panel</p>
        <h2>Dla kogo wyświetlić ekran?</h2>
        <div className="role-grid">
          <button
            type="button"
            className={selected === 'student' ? 'role-card role-card--active' : 'role-card'}
            onClick={() => pickRole('student')}
          >
            <strong>Student</strong>
            <small>plan zajęć, sala, prowadzący i aktualny komunikat</small>
          </button>
          <button
            type="button"
            className={selected === 'teacher' ? 'role-card role-card--active' : 'role-card'}
            onClick={() => pickRole('teacher')}
          >
            <strong>Prowadzący</strong>
            <small>status sali, czas zajęć i szybka edycja komunikatu</small>
          </button>
        </div>
      </div>
    </div>
  )
}
