import ClockCard from './ClockCard.jsx'

export default function TopControls({ dateTime, label }) {
  return (
    <div className="top-controls">
      <ClockCard />
      <time className="date-label" dateTime={dateTime}>{label}</time>
    </div>
  )
}
