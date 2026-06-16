import React from 'react'
import { formatShortDate } from './utils/date.js'
import MenuButton from './components/MenuButton.jsx'
import RoleMenu from './components/RoleMenu.jsx'
import LogoPanel from './components/LogoPanel.jsx'
import TopControls from './components/TopControls.jsx'
import LessonInfo from './components/LessonInfo.jsx'
import CommunicationBox from './components/CommunicationBox.jsx'

const API_URL = 'http://localhost:8000'

const fallbackData = {
  room: 'SALA WOLNA',
  subject: '',
  teacher: '-',
  direction: '-',
  duration: '-',
  status: 'Brak aktywnych zajęć',
  message: 'Przyłóż kartę RFID, aby zalogować obecność.'
}

export default function App() {
  const [menuOpen, setMenuOpen] = React.useState(false)
  const [now, setNow] = React.useState(new Date())
  const [data, setData] = React.useState(fallbackData)

  const loadPanelData = React.useCallback(async () => {
    try {
      const response = await fetch(`${API_URL}/api/panel`)

      if (!response.ok) {
        throw new Error('Błąd odpowiedzi API')
      }

      const panelData = await response.json()
      setData(panelData)
    } catch (error) {
      setData({
        room: 'Błąd',
        subject: 'Nie udało się pobrać danych',
        teacher: '-',
        direction: '-',
        duration: '-',
        status: 'Brak połączenia',
        message: 'Sprawdź, czy backend FastAPI działa na porcie 8000.'
      })
    }
  }, [])

  React.useEffect(() => {
    const timer = setInterval(() => setNow(new Date()), 1000)
    return () => clearInterval(timer)
  }, [])

  React.useEffect(() => {
    loadPanelData()

    const interval = setInterval(loadPanelData, 1000)
    return () => clearInterval(interval)
  }, [loadPanelData])

  const handleSessionSelected = async () => {
    setMenuOpen(false)
    await loadPanelData()
  }

  return (
    <main className="page-shell">
      <section className="device-frame">
        <MenuButton onOpen={() => setMenuOpen(true)} />

        <RoleMenu
          open={menuOpen}
          apiUrl={API_URL}
          onSessionSelected={handleSessionSelected}
          onClose={() => setMenuOpen(false)}
        />

        <div className="dashboard-layout">
          <LogoPanel />
          <TopControls dateTime={now.toISOString()} label={formatShortDate(now)} />
          <LessonInfo data={data} mode="student" />
          <CommunicationBox message={data.message} />
        </div>
      </section>
    </main>
  )
}