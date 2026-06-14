import React from 'react'

export default function ClockCard() {
  const [now, setNow] = React.useState(new Date())

  React.useEffect(() => {
    const timer = setInterval(() => setNow(new Date()), 1000)
    return () => clearInterval(timer)
  }, [])

  const hourAngle = (now.getHours() % 12) * 30 + now.getMinutes() * 0.5
  const minuteAngle = now.getMinutes() * 6 + now.getSeconds() * 0.1
  const secondAngle = now.getSeconds() * 6
  const digital = now.toLocaleTimeString('pl-PL', { hour: '2-digit', minute: '2-digit' })

  return (
    <section className="clock-card" aria-label="Zegar">
      <div className="clock-face">
        {Array.from({ length: 12 }, (_, index) => (
          <span key={index} className="clock-face__tick" style={{ transform: `translateX(-50%) rotate(${index * 30}deg)` }} />
        ))}
        <span className="clock-face__hand clock-face__hand--hour" style={{ transform: `translateX(-50%) rotate(${hourAngle}deg)` }} />
        <span className="clock-face__hand clock-face__hand--minute" style={{ transform: `translateX(-50%) rotate(${minuteAngle}deg)` }} />
        <span className="clock-face__hand clock-face__hand--second" style={{ transform: `translateX(-50%) rotate(${secondAngle}deg)` }} />
        <span className="clock-face__center" />
      </div>
      <strong className="clock-card__time">{digital}</strong>
    </section>
  )
}
