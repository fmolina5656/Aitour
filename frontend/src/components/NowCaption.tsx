import { LANE_META, laneColor } from '../agents'
import type { StageState } from '../types'

/** El turno actual en letra grande: lo que se lee de lejos. */
export function NowCaption({ s, onOpenOnePager }: { s: StageState; onOpenOnePager: () => void }) {
  if (s.phase === 'idle') {
    return (
      <div className="now">
        <div className="now-who muted">Esperando visitante</div>
        <div className="now-text muted">Cuéntanos un problema real de tu empresa y un equipo de agentes de IA armará la solución en vivo.</div>
      </div>
    )
  }
  if (s.live) {
    const meta = LANE_META[s.live.agent]
    return (
      <div className="now">
        <div className="now-who" style={{ color: laneColor(s.live.agent) }}>
          {meta.label} <span className="muted">{meta.thinking}…</span>
        </div>
        <div className="now-text">{s.live.text || ' '}</div>
      </div>
    )
  }
  const last = s.turns[s.turns.length - 1]
  if (!last) return null
  return (
    <div className="now">
      <div className="now-who" style={{ color: laneColor(last.lane) }}>
        {LANE_META[last.lane].label} · <span className={last.kind === 'object' ? 'alert' : ''}>{last.action}</span>
      </div>
      <div className="now-text">{last.text}</div>
      {s.phase === 'done' && s.onepager && (
        <div className="now-actions">
          <button className="btn" onClick={onOpenOnePager}>
            Ver one-pager <kbd>O</kbd>
          </button>
        </div>
      )}
    </div>
  )
}
