export type AgentId = 'arquitecto' | 'financiero' | 'riesgo' | 'redactor'

export interface StageEvent<T = Record<string, unknown>> {
  type: string
  data: T
  session_id?: string | null
  t?: number
}

export interface Bubble {
  agent: AgentId
  text: string
  final: boolean
  objection?: boolean
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

export interface Objection {
  de: AgentId
  para: AgentId
  motivo: string
  propuesta: string
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

export interface StageState {
  connected: boolean
  mode: string
  sessionId: string | null
  phase: 'idle' | 'swarm' | 'done'
  brief: Record<string, string> | null
  thinking: AgentId | null
  bubbles: Partial<Record<AgentId, Bubble>>
  feed: Bubble[]
  lastSpeaker: AgentId | null
  objection: Objection | null
  spans: Span[]
  sessionCost: number
  governance: GovEvent[]
  diagram: { mermaid: string; version: number; cambios?: string | null } | null
  cost: Cost | null
  costHistory: number[]
  onepager: OnePager | null
  elapsed: number
  budget: number
}
