export default function LessonInfo({ data, mode }) {
  return (
    <section className="lesson-card" aria-label="Informacje o zajęciach">
      <p className="lesson-card__badge">{mode === 'student' ? 'Widok studenta' : 'Widok prowadzącego'}</p>
      <h1 className="lesson-card__room">{data.room}</h1>
      <h2 className="lesson-card__subject">{data.subject}</h2>
      <dl className="info-grid">
        <InfoBox label="Prowadzący" value={data.teacher} />
        <InfoBox label="Kierunek" value={data.direction} extraClass="info-box--wide" />
        <InfoBox label="Czas trwania" value={data.duration} />
      </dl>
      <span className="status-pill">{data.status}</span>
    </section>
  )
}

function InfoBox({ label, value, extraClass = '' }) {
  return (
    <div className={`info-box ${extraClass}`.trim()}>
      <dt className="info-box__label">{label}</dt>
      <dd className="info-box__value">{value}</dd>
    </div>
  )
}
