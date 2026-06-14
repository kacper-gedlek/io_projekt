import React from 'react'
import { studentPlan, teacherPlan } from './data/schedule.js'
import { formatShortDate } from './utils/date.js'
import MenuButton from './components/MenuButton.jsx'
import RoleMenu from './components/RoleMenu.jsx'
import LogoPanel from './components/LogoPanel.jsx'
import TopControls from './components/TopControls.jsx'
import LessonInfo from './components/LessonInfo.jsx'
import CommunicationBox from './components/CommunicationBox.jsx'

export default function App() {
  const [mode, setMode] = React.useState('student')
  const [menuOpen, setMenuOpen] = React.useState(false)
  const [now, setNow] = React.useState(new Date())

  React.useEffect(() => {
    const timer = setInterval(() => setNow(new Date()), 1000)
    return () => clearInterval(timer)
  }, [])

  const data = mode === 'student' ? studentPlan : teacherPlan

  return (
    <main className="page-shell">
      <section className="device-frame">
        <MenuButton onOpen={() => setMenuOpen(true)} />
        <RoleMenu selected={mode} onSelect={setMode} open={menuOpen} onClose={() => setMenuOpen(false)} />

        <div className="dashboard-layout">
          <LogoPanel />
          <TopControls dateTime={now.toISOString()} label={formatShortDate(now)} />
          <LessonInfo data={data} mode={mode} />
          <CommunicationBox message={data.message} />
        </div>
      </section>
    </main>
  )
}
