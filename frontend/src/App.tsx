import { useEffect, useRef, useState } from 'react'
import { ChatLog, ShareCard } from './components/ChatLog'
import { CostPanel } from './components/CostPanel'
import { ArchitecturePanel } from './components/ArchitecturePanel'
import { GovernancePanel } from './components/GovernancePanel'
import { OnePagerOverlay } from './components/OnePagerOverlay'
import { Subtitle } from './components/Subtitle'
import { TextInput } from './components/TextInput'
import { BriefCard, VoiceBar } from './components/VoiceUI'
import { Scene } from './scene/Scene'
import { api, useStage } from './useStage'
import { useVoice } from './voice/useVoice'

// Versión del logo para fondo oscuro (la palabra "Ready" en blanco); se puede reemplazar por VITE_BRAND_LOGO_URL.
const LOGO_URL = (import.meta.env.VITE_BRAND_LOGO_URL as string | undefined) ?? '/brand/readymind-logo-dark.png'

// Modo tablet (tecla M): solo el universo y un subtítulo. Se recuerda entre recargas.
const TABLET_KEY = 'aitour.tablet'
function readTablet() {
  try {
    return localStorage.getItem(TABLET_KEY) === '1'
  } catch {
    return false
  }
}

export default function App() {
  const s = useStage()
  const [tablet, setTablet] = useState(readTablet)
  const [showText, setShowText] = useState(false)
  const [showOnePager, setShowOnePager] = useState(false)
  const [focusText, setFocusText] = useState(0)
  const voice = useVoice()
  const interviewing = voice.active || s.interview.active
  // el manejador de teclado lee siempre el estado más reciente
  const latest = useRef({ s, voice, interviewing })
  latest.current = { s, voice, interviewing }

  useEffect(() => {
    setShowOnePager(false)
  }, [s.sessionId])

  useEffect(() => {
    try {
      localStorage.setItem(TABLET_KEY, tablet ? '1' : '0')
    } catch {
      // sin almacenamiento: el modo vale solo para esta carga
    }
  }, [tablet])

  useEffect(() => {
    const onKey = (e: KeyboardEvent) => {
      const typing = e.target instanceof HTMLInputElement || e.target instanceof HTMLTextAreaElement
      if (e.key === 'Escape') {
        setShowText(false)
        setShowOnePager(false)
      }
      if (typing) return
      const { s, voice, interviewing } = latest.current
      const k = e.key.toLowerCase()
      if (k === 'r') {
        setShowText(false)
        void voice.stop()
        api.reset()
      } else if (k === 'v' && !interviewing) {
        void voice.start()
      } else if (k === 'enter' && s.interview.proposed) {
        voice.confirm()
      } else if (k === 't') {
        e.preventDefault()
        if (interviewing) setFocusText((n) => n + 1)
        else setShowText(true)
      } else if (k === 'p') {
        // operador: si se cae la red, reproduce ya una sesión grabada real
        void voice.stop()
        api.replay()
      } else if (k === 'o') {
        setShowOnePager((v) => !v)
      } else if (k === 'm') {
        setTablet((v) => !v)
      } else if (k === 'f') {
        if (document.fullscreenElement) document.exitFullscreen()
        else document.documentElement.requestFullscreen()
      }
    }
    window.addEventListener('keydown', onKey)
    return () => window.removeEventListener('keydown', onKey)
  }, [])

  return (
    <>
    <Scene s={s} tablet={tablet} />
    {tablet ? (
      <div className="stage tablet">
        {s.phase === 'idle' && !interviewing && (
          // en el stand hay ruido: escribir es lo principal y la voz queda como alternativa
          <div className="scene-cta">
            <button className="btn primary big" onClick={() => setShowText(true)}>
              ✍️ Escribe tu problema
            </button>
            <button className="btn big" onClick={() => void voice.start()}>
              🎙 Prefiero hablar
            </button>
          </div>
        )}
        {/* sin micrófono hace falta la entrada de texto; con micrófono basta el núcleo que escucha */}
        {interviewing && s.phase === 'idle' && voice.status === 'text-only' && (
          <VoiceBar s={s} status={voice.status} onText={voice.sendText} focusText={focusText} />
        )}
        {s.interview.proposed && (
          <BriefCard brief={s.interview.proposed} onConfirm={voice.confirm} onCorrect={() => setFocusText((n) => n + 1)} />
        )}
        {/* el QR va a la esquina: abajo al centro tapaba a los mundos */}
        <div className="tablet-share">
          <ShareCard s={s} onOpenOnePager={() => setShowOnePager(true)} />
        </div>
        <div className="tablet-bottom">
          <Subtitle s={s} />
        </div>
        {showText && <TextInput onClose={() => setShowText(false)} />}
        {s.onepager && showOnePager && (
          <OnePagerOverlay op={s.onepager} qrUrl={s.share?.qrUrl} diagramSvg={s.diagram?.svg} onClose={() => setShowOnePager(false)} />
        )}
      </div>
    ) : (
    <div className="stage">
      <header className="header">
        <div className="brand">
          <img src={LOGO_URL} alt="Readymind" className="logo" />
          <span className="title">
            Cuéntame tu problema y <span className="brand-gradient-text">en 3 minutos te armo la solución</span>
          </span>
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

      {s.phase === 'idle' && !interviewing && (
        <div className="scene-cta">
          <button className="btn primary big" onClick={() => void voice.start()}>
            🎙 Háblame de tu problema <kbd>V</kbd>
          </button>
          <button className="btn" onClick={() => setShowText(true)}>
            Prefiero escribir <kbd>T</kbd>
          </button>
        </div>
      )}
      {interviewing && s.phase === 'idle' && <VoiceBar s={s} status={voice.status} onText={voice.sendText} focusText={focusText} />}
      {s.interview.proposed && (
        <BriefCard brief={s.interview.proposed} onConfirm={voice.confirm} onCorrect={() => setFocusText((n) => n + 1)} />
      )}
      <ChatLog s={s} onOpenOnePager={() => setShowOnePager(true)} />
      <section className="results">
        <ArchitecturePanel s={s} />
        <CostPanel s={s} />
        <GovernancePanel s={s} />
      </section>

      <footer className="footer">
        <span>Microsoft Foundry · Microsoft Agent Framework</span>
        <span className="keys">
          <kbd>V</kbd> hablar <kbd>T</kbd> escribir <kbd>O</kbd> one-pager <kbd>R</kbd> reiniciar <kbd>M</kbd> modo tablet <kbd>F</kbd> pantalla completa
        </span>
      </footer>

      {showText && <TextInput onClose={() => setShowText(false)} />}
      {s.onepager && showOnePager && (
        <OnePagerOverlay op={s.onepager} qrUrl={s.share?.qrUrl} diagramSvg={s.diagram?.svg} onClose={() => setShowOnePager(false)} />
      )}
    </div>
    )}
    </>
  )
}
