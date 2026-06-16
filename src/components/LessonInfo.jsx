export default function LessonInfo({ data }) {
  return (
    <section className="lesson-card" aria-label="Informacje o zajęciach">
      <h1 className="lesson-card__room">{data.room}</h1>
      <h2 className="lesson-card__subject">{data.subject}</h2>

      <dl className="info-grid">
        <InfoBox label="Prowadzący" value={data.teacher} />
        <InfoBox label="Zajęcia" value={data.direction} extraClass="info-box--wide" />
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