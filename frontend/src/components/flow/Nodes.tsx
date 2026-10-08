import { Handle, Position, type NodeProps } from '@xyflow/react'
import type { LucideIcon } from 'lucide-react'
import { Check, TriangleAlert } from 'lucide-react'
import type { NodeStatus } from '../../types'

export interface AgentNodeData extends Record<string, unknown> {
  label: string
  role: string
  icon: LucideIcon
  color: string
  status: NodeStatus
  chip?: string
  variant: 'trigger' | 'agent' | 'output'
}

export interface SubNodeData extends Record<string, unknown> {
  label: string
  caption: string
  icon: LucideIcon
  color: string
  pulse: number
}

const hidden = { opacity: 0 }

/** Nodo principal estilo n8n: ícono grande, etiqueta debajo, estado en el borde. */
export function AgentNode({ data }: NodeProps) {
  const n = data as AgentNodeData
  const Icon = n.icon
  return (
    <div className={`an an-${n.variant} st-${n.status}`} style={{ ['--c' as string]: n.color }}>
      <Handle type="target" position={Position.Left} id="in" style={hidden} />
      <Handle type="source" position={Position.Right} id="out" style={hidden} />
      <Handle type="target" position={Position.Top} id="top-in" style={hidden} />
      <Handle type="source" position={Position.Top} id="top-out" style={hidden} />
      <Handle type="source" position={Position.Bottom} id="bottom" style={hidden} />
      <div className="an-box">
        {n.status === 'running' && <span className="an-ring" />}
        <Icon className="an-icon" strokeWidth={1.6} />
        {n.status === 'done' && (
          <span className="an-badge ok">
            <Check size={16} strokeWidth={3} />
          </span>
        )}
        {n.status === 'objected' && (
          <span className="an-badge warn">
            <TriangleAlert size={15} strokeWidth={2.6} />
          </span>
        )}
      </div>
      <div className="an-label">{n.label}</div>
      <div className={`an-chip ${n.chip ? 'has' : ''}`}>{n.chip ?? n.role}</div>
    </div>
  )
}

/** Sub-nodo (modelo o herramienta) colgado del agente, como en el nodo AI Agent de n8n. */
export function SubNode({ data }: NodeProps) {
  const n = data as SubNodeData
  const Icon = n.icon
  return (
    <div className="sn" style={{ ['--c' as string]: n.color }}>
      <Handle type="target" position={Position.Top} id="in" style={hidden} />
      <div className={`sn-circle ${n.pulse ? 'used' : ''}`}>
        {n.pulse > 0 && <span key={n.pulse} className="sn-ping" />}
        <Icon className="sn-icon" strokeWidth={1.7} />
      </div>
      <div className="sn-label">{n.label}</div>
      <div className="sn-caption">{n.caption}</div>
    </div>
  )
}
