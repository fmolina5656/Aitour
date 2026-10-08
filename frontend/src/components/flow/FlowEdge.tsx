import { BaseEdge, EdgeLabelRenderer, getBezierPath, type EdgeProps } from '@xyflow/react'
import { Particle } from './Particle'

export interface FlowEdgeData extends Record<string, unknown> {
  active: boolean
  objection: boolean
  arc: boolean
  sub: boolean
  pulses: number[]
  label?: string
}

/**
 * Cable estilo n8n. Hacia adelante: bezier horizontal. Hacia atrás o salteando nodos: arco por encima.
 * Cada traspaso agrega un "pulse" que dispara una bolita a lo largo del cable.
 */
export function FlowEdge({ id, sourceX, sourceY, targetX, targetY, sourcePosition, targetPosition, data }: EdgeProps) {
  const e = data as FlowEdgeData
  let d: string
  let lx: number
  let ly: number
  if (e.arc) {
    const h = 110 + Math.abs(targetX - sourceX) * 0.16
    d = `M${sourceX},${sourceY} C${sourceX},${sourceY - h} ${targetX},${targetY - h} ${targetX},${targetY}`
    lx = (sourceX + targetX) / 2
    ly = Math.min(sourceY, targetY) - h * 0.75
  } else {
    ;[d, lx, ly] = getBezierPath({ sourceX, sourceY, targetX, targetY, sourcePosition, targetPosition, curvature: 0.35 })
  }
  const color = e.objection ? 'var(--alert)' : e.sub ? 'var(--text-2)' : 'var(--accent)'
  const cls = ['fe', e.active && 'fe-active', e.objection && 'fe-objection', e.sub && 'fe-sub'].filter(Boolean).join(' ')
  return (
    <>
      <BaseEdge id={id} path={d} className={cls} />
      {e.active && !e.sub && <path d={d} className={`fe-flow ${e.objection ? 'fe-flow-alert' : ''}`} />}
      {e.pulses.slice(-2).map((p) => (
        <Particle key={p} d={d} color={color} duration={e.sub ? 650 : 1150} />
      ))}
      {e.label && (
        <EdgeLabelRenderer>
          <div className={`fe-label ${e.objection ? 'fe-label-alert' : ''}`} style={{ transform: `translate(-50%, -50%) translate(${lx}px, ${ly}px)` }}>
            {e.label}
          </div>
        </EdgeLabelRenderer>
      )}
    </>
  )
}
