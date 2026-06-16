import React from 'react'

export default function RoleMenu({
  open,
  apiUrl,
  onSessionSelected,
  onClose
}) {
  const [step, setStep] = React.useState('scan-teacher')
  const [statusText, setStatusText] = React.useState('')
  const [sessions, setSessions] = React.useState([])
  const [loading, setLoading] = React.useState(false)

  React.useEffect(() => {
    if (!open) {
      setStep('scan-teacher')
      setStatusText('')
      setSessions([])
      setLoading(false)
      return
    }

    async function startTeacherAuth() {
      setLoading(true)
      setStatusText('Przyłóż kartę RFID prowadzącego...')

      try {
        await fetch(`${apiUrl}/api/teacher/auth/start`, { method: 'POST' })
        setStep('scan-teacher')
      } catch (error) {
        setStatusText('Nie udało się rozpocząć autoryzacji prowadzącego.')
      } finally {
        setLoading(false)
      }
    }

    startTeacherAuth()
  }, [open, apiUrl])

  React.useEffect(() => {
    if (!open || step !== 'scan-teacher') return

    let cancelled = false

    async function pollTeacherAuth() {
      try {
        const response = await fetch(`${apiUrl}/api/teacher/auth/status`)
        const data = await response.json()

        if (cancelled) return

        if (data.status === 'authorized') {
          const sortedSessions = [...(data.sessions || [])].sort((a, b) => {
            const first = Number(a.sessdate || 0)
            const second = Number(b.sessdate || 0)
            return first - second
  })

          setSessions(sortedSessions)
          setStep('select-session')
          setStatusText('')
          return
        }

        if (data.status === 'rejected') {
          await fetch(`${apiUrl}/api/teacher/auth/cancel`, { method: 'POST' })
          onClose()
          return
        }

        setStatusText('Oczekiwanie na kartę prowadzącego...')
      } catch (error) {
        if (!cancelled) {
          setStatusText('Błąd połączenia z backendem.')
        }
      }
    }

    pollTeacherAuth()
    const interval = setInterval(pollTeacherAuth, 1000)

    return () => {
      cancelled = true
      clearInterval(interval)
    }
  }, [open, step, apiUrl, onClose])

  if (!open) return null

  const closeMenu = async () => {
    try {
      await fetch(`${apiUrl}/api/teacher/auth/cancel`, { method: 'POST' })
    } catch (error) {
      // Zamykamy modal nawet jeśli backend nie odpowie.
    }

    onClose()
  }

  const pickSession = async (session) => {
    setLoading(true)

    try {
      const response = await fetch(`${apiUrl}/api/teacher/select-session`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          course_id: session.course_id,
          session_id: session.id
        })
      })

      if (!response.ok) {
        throw new Error('Błąd wyboru sesji')
      }

      onSessionSelected()
    } catch (error) {
      setStatusText('Nie udało się wybrać zajęć.')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="menu-overlay" role="dialog" aria-modal="true" aria-label="Rozpoczęcie zajęć">
      <div className="role-menu">
        <button className="close-btn" type="button" onClick={closeMenu} aria-label="Zamknij menu">×</button>

        {step === 'scan-teacher' && (
          <>
            <p className="menu-eyebrow">Rozpoczęcie zajęć</p>
            <h2>Przyłóż kartę RFID prowadzącego</h2>
            <p className="menu-status">{statusText || 'Oczekiwanie na kartę prowadzącego...'}</p>
          </>
        )}

        {step === 'select-session' && (
          <>
            <p className="menu-eyebrow">Wybierz zajęcia</p>
            <h2>Które zajęcia chcesz rozpocząć?</h2>

            {statusText && <p className="menu-status">{statusText}</p>}

            <div className="session-list">
              {sessions.length === 0 && (
                <p className="menu-status">Nie znaleziono zajęć dla prowadzącego.</p>
              )}

              {sessions.map((session) => (
                <button
                  key={`${session.course_id}-${session.id}`}
                  type="button"
                  className="session-card"
                  onClick={() => pickSession(session)}
                  disabled={loading}
                >
                  <strong>{session.course_name || 'Kurs Moodle'}</strong>
                  <small>{session.attendance_name || 'Zajęcia'}</small>
                  <span>{session.label || `${session.date || ''} ${session.time_start || ''}–${session.time_end || ''}`}</span>
                </button>
              ))}
            </div>
          </>
        )}
      </div>
    </div>
  )
}