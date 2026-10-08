import type { Actor, AgentId, FlowNodeId } from './types'

export const AGENTS: AgentId[] = ['arquitecto', 'financiero', 'riesgo', 'diagramador', 'redactor']

export const ACTOR_META: Record<Actor, { label: string; role: string; thinking: string }> = {
  visitante: { label: 'Visitante', role: 'Cuenta el problema', thinking: '' },
  arquitecto: { label: 'Arquitecto', role: 'Diseña en Azure', thinking: 'diseñando la solución' },
  financiero: { label: 'Financiero', role: 'Estima el costo', thinking: 'revisando el costo' },
  riesgo: { label: 'Riesgo', role: 'Datos y regulación', thinking: 'revisando datos y regulación' },
  diagramador: { label: 'Diagramador', role: 'Dibuja la arquitectura', thinking: 'diagramando la arquitectura en Azure' },
  redactor: { label: 'Redactor', role: 'Resumen ejecutivo', thinking: 'escribiendo el one-pager' },
}

export const nodeColor = (n: FlowNodeId) => `var(--who-${n})`

export const usd = (n: number) =>
  n.toLocaleString('es-MX', { style: 'currency', currency: 'USD', maximumFractionDigits: 0 })

/** Formato corto para los nodos: $4,972 */
export const money = (n: number) => `$${Math.round(n).toLocaleString('es-MX')}`
