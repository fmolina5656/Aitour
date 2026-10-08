import { useEffect, useState } from 'react'
import { Conversation } from './components/Conversation'
import { CostPanel } from './components/CostPanel'
import { Diagram } from './components/Diagram'
import { GovernancePanel } from './components/GovernancePanel'
import { NowCaption } from './components/NowCaption'
import { OnePagerOverlay } from './components/OnePagerOverlay'
import { TextInput } from './components/TextInput'
import { api, useStage } from './useStage'

const LOGO_URL = import.meta.env.VITE_BRAND_LOGO_URL as string | undefined

export default function App() {
  const s = useStage()
  const [showText, setShowText] = useState(false)
  const [showOnePager, setShowOnePager] = useState(false)

  useEffect(() => setShowOnePager(false), [s.sessionId])

  useEffect(() => {
    const onKey = (e: KeyboardEvent) => {
      const typing = e.target instanceof HTMLInputElement || e.target instanceof HTMLTextAreaElement
      if (e.key === 'Escape') {
        setShowText(false)
        setShowOnePager(false)
      }
      if (typing) return
      const k = e.key.toLowerCase()
      if (k === 'r') {
        setShowText(false)
        api.reset()
      } else if (k === 't') {
        e.preventDefault()
        setShowText(true)
      } else if (k === 'o') {
        setShowOnePager((v) => !v)
      } else if (k === 'f') {
        if (document.fullscreenElement) document.exitFullscreen()
        else document.documentElement.requestFullscreen()
      }
    }
    window.addEventListener('keydown', onKey)
    return () => window.removeEventListener('keydown', onKey)
  }, [])

  return (
    <div className="stage">
      <header className="header">
        <div className="brand">
          {LOGO_URL ? <img src={LOGO_URL} alt="Readymind" className="logo" /> : <span className="logo-text">readymind</span>}
          <span className="title">Cuéntame tu problema y en 3 minutos te armo la solución</span>
        </div>
        <div className="status">
          {s.mode === 'replay' && <span>Sesión grabada</span>}
          {s.mode === 'mock' && <span>Modo simulado</span>}
          {!s.connected && <span className="alert">Sin conexión</span>}
          {s.phase !== 'idle' && (
            <span className="clock">
              {Math.floor(s.elapsed)}s <span className="muted">/ {s.budget}s</span>
            </span>
          )}
        </div>
      </header>

      <main className="main">
        <section className="left">
          <Conversation s={s} />
          <NowCaption s={s} onOpenOnePager={() => setShowOnePager(true)} />
        </section>
        <aside className="right">
          <Diagram code={s.diagram?.mermaid ?? null} version={s.diagram?.version} />
          <CostPanel s={s} />
          <GovernancePanel s={s} />
        </aside>
      </main>

      <footer className="footer">
        <span>Microsoft Foundry · Microsoft Agent Framework</span>
        <span className="keys">
          <kbd>T</kbd> escribir <kbd>O</kbd> one-pager <kbd>R</kbd> reiniciar <kbd>F</kbd> pantalla completa
        </span>
      </footer>

      {showText && <TextInput onClose={() => setShowText(false)} />}
      {s.onepager && showOnePager && <OnePagerOverlay op={s.onepager} onClose={() => setShowOnePager(false)} />}
    </div>
  )
}
