import { useLayoutEffect, useRef, useState } from 'react'
import { LANES, LANE_META, laneColor } from '../agents'
import type { Lane, StageState, Turn } from '../types'

const LABEL_W = 180
const MIN_COLS = 7
const GAP = 10

interface Box {
  x: number
  y: number
  w: number
  h: number
}

/**
 * Conversación en carriles: una fila por participante, los turnos avanzan de izquierda a derecha.
 * Las líneas muestran quién le responde a quién; las objeciones son punteadas.
 */
export function Conversation({ s }: { s: StageState }) {
  const ref = useRef<HTMLDivElement>(null)
  const [size, setSize] = useState({ w: 1200, h: 520 })
  useLayoutEffect(() => {
    if (!ref.current) return
    const ro = new ResizeObserver(([e]) => setSize({ w: e.contentRect.width, h: e.contentRect.height }))
    ro.observe(ref.current)
    return () => ro.disconnect()
  }, [])

  const items: (Turn & { pending?: boolean })[] = [...s.turns]
  if (s.live) items.push({ lane: s.live.agent, kind: 'propose', action: LANE_META[s.live.agent].thinking, text: '', pending: true })

  const cols = Math.max(MIN_COLS, items.length)
  const colW = (size.w - LABEL_W) / cols
  const laneH = size.h / LANES.length
  const box = (i: number, lane: Lane): Box => ({
    x: LABEL_W + i * colW + GAP / 2,
    y: LANES.indexOf(lane) * laneH + GAP,
    w: colW - GAP,
    h: laneH - GAP * 2,
  })
  const boxes = items.map((t, i) => box(i, t.lane))

  return (
    <div className="conv" ref={ref}>
      {LANES.map((lane, i) => (
        <div key={lane} className="lane" style={{ top: i * laneH, height: laneH }}>
          <div className="lane-label">
            <span className="lane-mark" style={{ background: laneColor(lane) }} />
            <div>
              <div className="lane-name">{LANE_META[lane].label}</div>
              <div className="lane-role">{LANE_META[lane].role}</div>
            </div>
          </div>
        </div>
      ))}

      <svg className="conv-edges" width={size.w} height={size.h}>
        <defs>
          <marker id="arrow" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto">
            <path d="M0,0 L10,5 L0,10 z" fill="var(--line-strong)" />
          </marker>
          <marker id="arrow-alert" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto">
            <path d="M0,0 L10,5 L0,10 z" fill="var(--alert)" />
          </marker>
        </defs>
        {boxes.slice(1).map((b, k) => {
          const a = boxes[k]
          const from = items[k]
          const objection = from.kind === 'object'
          const x1 = a.x + a.w
          const y1 = a.y + a.h / 2
          const x2 = b.x
          const y2 = b.y + b.h / 2
          const mx = (x1 + x2) / 2
          return (
            <g key={k}>
              <path
                d={`M${x1},${y1} H${mx} V${y2} H${x2 - 2}`}
                className={`edge ${objection ? 'edge-alert' : ''} ${items[k + 1].pending ? 'edge-pending' : ''}`}
                markerEnd={`url(#${objection ? 'arrow-alert' : 'arrow'})`}
              />
              {objection && (
                <text x={mx + 6} y={(y1 + y2) / 2} className="edge-label">
                  objeción
                </text>
              )}
            </g>
          )
        })}
      </svg>

      {items.map((t, i) => (
        <TurnCard key={i} t={t} b={boxes[i]} n={i} latest={i === items.length - 1} />
      ))}
    </div>
  )
}

function TurnCard({ t, b, n, latest }: { t: Turn & { pending?: boolean }; b: Box; n: number; latest: boolean }) {
  return (
    <div
      className={`turn kind-${t.kind} ${t.pending ? 'pending' : ''} ${latest ? 'latest' : ''}`}
      style={{ left: b.x, top: b.y, width: b.w, height: b.h, ['--who' as string]: laneColor(t.lane) }}
    >
      <div className="turn-n">{n === 0 ? 'Inicio' : `Paso ${n}`}</div>
      <div className="turn-action">{t.pending ? '…' : t.action}</div>
      {t.chip && !t.pending && <div className="turn-chip">{t.chip}</div>}
    </div>
  )
}
