import { useEffect, useState } from 'react'
import { AgentGraph } from './components/AgentGraph'
import { CostPanel } from './components/CostPanel'
import { Diagram } from './components/Diagram'
import { GovernancePanel } from './components/GovernancePanel'
import { OnePagerOverlay } from './components/OnePagerOverlay'
import { TextInput } from './components/TextInput'
import { api, useStage } from './useStage'

const LOGO_URL = import.meta.env.VITE_BRAND_LOGO_URL as string | undefined

export default function App() {
  const s = useStage()
  const [showText, setShowText] = useState(false)
  const [hideOnePager, setHideOnePager] = useState(false)

  useEffect(() => setHideOnePager(false), [s.sessionId])

  useEffect(() => {
    const onKey = (e: KeyboardEvent) => {
      const typing = e.target instanceof HTMLInputElement || e.target instanceof HTMLTextAreaElement
      if (e.key === 'Escape') setShowText(false)
      if (typing) return
      const k = e.key.toLowerCase()
      if (k === 'r') {
        setShowText(false)
        api.reset()
      } else if (k === 't') {
        e.preventDefault()
        setShowText(true)
      } else if (k === 'f') {
        if (document.fullscreenElement) document.exitFullscreen()
        else document.documentElement.requestFullscreen()
      }
    }
    window.addEventListener('keydown', onKey)
    return () => window.removeEventListener('keydown', onKey)
  }, [])

  const remaining = Math.max(0, s.budget - s.elapsed)
  return (
    <div className="stage">
      <header className="header">
        <div className="brand">
          {LOGO_URL ? <img src={LOGO_URL} alt="Readymind" className="logo" /> : <span className="logo-text">readymind</span>}
          <span className="brand-sep" />
          <span className="tagline">Cuéntame tu problema y en 3 minutos te armo la solución</span>
        </div>
        <div className="header-right">
          {s.mode === 'replay' && <span className="mode-pill replay">● Sesión grabada</span>}
          {s.mode === 'mock' && <span className="mode-pill mock">● Modo simulado</span>}
          {!s.connected && <span className="mode-pill offline">● Sin conexión</span>}
          {s.phase === 'swarm' && (
            <span className={`clock ${remaining < 20 ? 'clock-warn' : ''}`}>
              ⏱ {Math.floor(s.elapsed)} s <span className="muted">/ {s.budget} s</span>
            </span>
          )}
          <span className="powered">Microsoft Foundry</span>
          <button className="btn ghost small" onClick={() => api.reset()} title="Reset (R)">
            ↺ Reset
          </button>
        </div>
      </header>

      <main className="main">
        <section className="center">
          <AgentGraph s={s} />
          {s.phase === 'idle' && (
            <button className="start-cta" onClick={() => setShowText(true)}>
              Presiona <kbd>T</kbd> para escribir tu problema
            </button>
          )}
        </section>
        <GovernancePanel s={s} />
      </main>

      <footer className="bottom">
        <Diagram code={s.diagram?.mermaid ?? null} version={s.diagram?.version} cambios={s.diagram?.cambios} />
        <CostPanel s={s} />
      </footer>

      {showText && <TextInput onClose={() => setShowText(false)} />}
      {s.onepager && s.phase === 'done' && !hideOnePager && <OnePagerOverlay op={s.onepager} onClose={() => setHideOnePager(true)} />}
    </div>
  )
}
