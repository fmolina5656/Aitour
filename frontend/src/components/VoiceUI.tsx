import { useEffect, useRef, useState } from 'react'
import type { StageState } from '../types'
import { audioLevel } from '../voice/audio'
import type { VoiceStatus } from '../voice/useVoice'

const FIELDS: [string, string][] = [
  ['problema', 'Problema'],
  ['industria', 'Industria'],
  ['volumen', 'Volumen'],
  ['datos', 'Datos disponibles'],
]

/** "Esto entendí": el visitante confirma (voz, botón o Enter) antes de que arranque el enjambre. */
export function BriefCard({ brief, onConfirm, onCorrect }: { brief: Record<string, string>; onConfirm: () => void; onCorrect: () => void }) {
  return (
    <div className="brief-card">
      <div className="brief-kicker">Esto entendí</div>
      <div className="brief-grid">
        {FIELDS.map(([k, label]) => (
          <div key={k} className={k === 'problema' ? 'brief-wide' : ''}>
            <div className="brief-label">{label}</div>
            <div className="brief-value">{brief[k] || '—'}</div>
          </div>
        ))}
      </div>
      <div className="brief-actions">
        <span className="muted">Di “sí” o</span>
        <button className="btn primary" onClick={onConfirm}>
          Sí, adelante <kbd>Enter</kbd>
        </button>
        <button className="btn" onClick={onCorrect}>
          Corregir <kbd>T</kbd>
        </button>
      </div>
    </div>
  )
}

/** Barra de la entrevista: estado del micrófono con medidor de nivel y entrada por teclado de respaldo. */
export function VoiceBar({ s, status, onText, focusText }: { s: StageState; status: VoiceStatus; onText: (t: string) => void; focusText: number }) {
  const meter = useRef<HTMLDivElement>(null)
  const input = useRef<HTMLInputElement>(null)
  const [text, setText] = useState('')

  useEffect(() => {
    let raf = 0
    const tick = () => {
      if (meter.current) meter.current.style.setProperty('--lvl', String(Math.max(audioLevel.mic, audioLevel.agent * 0.6)))
      raf = requestAnimationFrame(tick)
    }
    raf = requestAnimationFrame(tick)
    return () => cancelAnimationFrame(raf)
  }, [])

  useEffect(() => {
    if (focusText || status === 'text-only') input.current?.focus()
  }, [focusText, status])

  const label =
    status === 'connecting' ? 'Conectando con la recepcionista…' : status === 'text-only' ? 'Sin micrófono: escribe tu respuesta' : s.interview.agentLive ? 'La recepcionista está hablando' : 'Te escucho · habla con naturalidad'

  return (
    <div className="voice-bar">
      <div ref={meter} className={`voice-meter ${status === 'live' ? 'on' : ''}`}>
        {Array.from({ length: 5 }, (_, i) => (
          <span key={i} style={{ ['--i' as string]: i }} />
        ))}
      </div>
      <div className="voice-label">{label}</div>
      <form
        className="voice-text"
        onSubmit={(e) => {
          e.preventDefault()
          if (text.trim()) onText(text.trim())
          setText('')
        }}
      >
        <input ref={input} value={text} onChange={(e) => setText(e.target.value)} placeholder="…o escribe aquí (ruido de feria)" />
      </form>
    </div>
  )
}
