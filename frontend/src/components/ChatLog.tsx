import { useEffect, useRef } from 'react'
import { ACTOR_META, nodeColor } from '../agents'
import type { StageState, Turn } from '../types'

/** La charla entre agentes, en orden. El mensaje más reciente se ve más grande. */
export function ChatLog({ s, onOpenOnePager }: { s: StageState; onOpenOnePager: () => void }) {
  const end = useRef<HTMLDivElement>(null)
  useEffect(() => end.current?.scrollIntoView({ behavior: 'smooth', block: 'end' }), [s.turns.length, s.live?.text, s.phase])

  if (s.phase === 'idle' && !s.interview.active && !s.interview.lines.length) {
    return (
      <aside className="chat">
        <div className="chat-head">Conversación</div>
        <div className="chat-empty">
          <div className="chat-empty-title">Cuéntanos un problema real de tu empresa</div>
          <div className="muted">Un equipo de agentes de IA en Microsoft Foundry diseñará la solución, discutirá el costo y los riesgos, y te entregará un resumen ejecutivo.</div>
        </div>
      </aside>
    )
  }

  const latest = s.live || s.blocked ? -1 : s.turns.length - 1
  return (
    <aside className="chat">
      <div className="chat-head">Conversación</div>
      <div className="chat-list">
        {s.interview.lines.map((l, i) => (
          <div
            key={`iv-${i}`}
            className={`msg ${s.phase === 'idle' && !s.interview.agentLive && i === s.interview.lines.length - 1 ? 'latest' : ''}`}
            style={{ ['--c' as string]: l.who === 'recepcionista' ? 'var(--brand-green)' : 'var(--who-visitante)' }}
          >
            <div className="msg-head">{l.who === 'recepcionista' ? 'Recepcionista' : 'Visitante'}</div>
            <div className="msg-text">{l.text}</div>
          </div>
        ))}
        {s.interview.agentLive && (
          <div className="msg latest" style={{ ['--c' as string]: 'var(--brand-green)' }}>
            <div className="msg-head">
              Recepcionista <span className="msg-action typing">hablando</span>
            </div>
            <div className="msg-text">{s.interview.agentLive}</div>
          </div>
        )}
        {s.phase !== 'idle' && s.interview.lines.length > 0 && <div className="chat-sep">El equipo de agentes toma el caso</div>}
        {s.phase !== 'idle' && s.turns.map((t, i) => (
          <Msg key={i} t={t} latest={i === latest} />
        ))}
        {s.live && (
          <div className="msg latest" style={{ ['--c' as string]: nodeColor(s.live.agent) }}>
            <div className="msg-head">
              <span className="msg-dot" />
              {ACTOR_META[s.live.agent].label}
              <span className="msg-action typing">{ACTOR_META[s.live.agent].thinking}</span>
            </div>
            <div className="msg-text">{s.live.text || <span className="dots" />}</div>
          </div>
        )}
        {s.blocked && (
          <div className="msg latest system" style={{ ['--c' as string]: 'var(--brand-green)' }}>
            <div className="msg-head">
              Readymind
              <span className="msg-action">{s.blocked.kind === 'jailbreak' ? 'Prompt Shields bloqueó la solicitud' : 'Fuera de alcance'}</span>
            </div>
            <div className="msg-text">{s.blocked.reply}</div>
          </div>
        )}
        {s.phase === 'done' && s.onepager && (
          <div className="share">
            {s.share ? <img className="share-qr" src={s.share.qrUrl} alt="QR para recibir el one-pager" /> : null}
            <div className="share-text">
              <div className="share-title">{s.leadReceived ? '✓ ¡Recibido! Va en camino a tu correo' : 'Escanea y recibe tu one-pager en PDF'}</div>
              <div className="muted">{s.leadReceived ? 'Gracias por visitarnos.' : s.share ? 'Deja tu nombre, empresa y correo.' : 'Pídeselo a nuestro equipo en el stand.'}</div>
              <button className="btn" onClick={onOpenOnePager}>
                Ver one-pager <kbd>O</kbd>
              </button>
            </div>
          </div>
        )}
        <div ref={end} />
      </div>
    </aside>
  )
}

function Msg({ t, latest }: { t: Turn; latest: boolean }) {
  return (
    <div className={`msg ${latest ? 'latest' : ''} ${t.kind === 'object' ? 'objection' : ''}`} style={{ ['--c' as string]: nodeColor(t.actor) }}>
      <div className="msg-head">
        <span className="msg-dot" />
        {ACTOR_META[t.actor].label}
        <span className="msg-action">{t.action}</span>
      </div>
      <div className="msg-text">{t.text}</div>
    </div>
  )
}
