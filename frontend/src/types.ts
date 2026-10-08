export type AgentId = 'arquitecto' | 'financiero' | 'riesgo' | 'diagramador' | 'redactor'
export type Actor = 'visitante' | AgentId
export type FlowNodeId = Actor | 'onepager'
export type ToolId = 'calc' | 'normas' | 'catalogo'

export interface StageEvent<T = Record<string, unknown>> {
  type: string
  data: T
  session_id?: string | null
  t?: number
}

export type TurnKind = 'brief' | 'propose' | 'adjust' | 'object' | 'approve' | 'draw' | 'write'

/** Un mensaje de la conversación: quién, qué hizo y qué produjo. */
export interface Turn {
  actor: Actor
  kind: TurnKind
  action: string
  text: string
  chip?: string
}

export type NodeStatus = 'idle' | 'running' | 'done' | 'objected'

/** Un traspaso entre nodos: genera (o reutiliza) un cable y lanza una partícula. */
export interface Handoff {
  from: FlowNodeId
  to: FlowNodeId
  objection: boolean
  seq: number
}

export interface Span {
  agent: AgentId
  model: string
  input_tokens: number
  output_tokens: number
  latency_ms: number
  cost_usd: number
  session_cost_usd: number
}

export interface GovEvent {
  kind: string
  severity: 'info' | 'warning' | 'error'
  title: string
  detail: string
}

export interface CostItem {
  id: string
  servicio: string
  nombre: string
  categoria: string
  cantidad: number
  unidad: string
  precio_unitario: number
  costo_usd: number
  supuesto: string
  premium: boolean
}

export interface Cost {
  items: CostItem[]
  total_usd: number
  disclaimer: string
  vigencia: string
  version: number
}

export interface OnePager {
  status: string
  onepager: {
    titulo: string
    problema: string
    solucion: string
    beneficios: string[]
    riesgos_y_mitigaciones: string[]
    siguientes_pasos: string[]
  }
  costo: Cost | null
  mermaid: string
}

export interface InterviewLine {
  who: 'recepcionista' | 'visitante'
  text: string
}

export interface Interview {
  active: boolean
  lines: InterviewLine[]
  agentLive: string
  proposed: Record<string, string> | null
}

export interface StageState {
  connected: boolean
  mode: string
  models: Partial<Record<AgentId, string>>
  sessionId: string | null
  phase: 'idle' | 'swarm' | 'done'
  brief: Record<string, string> | null
  turns: Turn[]
  live: { agent: AgentId; text: string } | null
  lastActor: Actor | null
  status: Partial<Record<FlowNodeId, NodeStatus>>
  chips: Partial<Record<FlowNodeId, string>>
  handoffs: Handoff[]
  /** contador de llamadas por sub-nodo (modelo de cada agente o herramienta) para hacerlos "latir" */
  subPulses: Record<string, number>
  spans: Span[]
  sessionCost: number
  governance: GovEvent[]
  /** diagrama en SVG (layout del backend): automático en cada versión del Arquitecto; al final, el del Diagramador */
  diagram: { svg: string; version: number; por: 'arquitecto' | 'diagramador'; titulo?: string; pasos?: string[] } | null
  cost: Cost | null
  prevCost: Cost | null
  onepager: OnePager | null
  blocked: { kind: 'jailbreak' | 'off_topic'; reply: string } | null
  interview: Interview
  share: { qrUrl: string } | null
  leadReceived: boolean
  elapsed: number
  budget: number
}
