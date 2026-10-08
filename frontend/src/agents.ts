import type { AgentId } from './types'

export const AGENTS: Record<AgentId, { label: string; role: string; icon: string; x: number; y: number }> = {
  // posiciones en % del área del grafo
  arquitecto: { label: 'Arquitecto', role: 'Diseña en Azure / Foundry', icon: '◆', x: 9, y: 30 },
  financiero: { label: 'Financiero', role: 'Estima el costo mensual', icon: '$', x: 91, y: 30 },
  riesgo: { label: 'Riesgo', role: 'LFPDPPP y seguridad', icon: '⛨', x: 9, y: 80 },
  redactor: { label: 'Redactor', role: 'One-pager ejecutivo', icon: '✎', x: 91, y: 80 },
}

export const AGENT_ORDER: AgentId[] = ['arquitecto', 'financiero', 'riesgo', 'redactor']

export const agentColor = (a: AgentId) => `var(--agent-${a})`

export const usd = (n: number, digits = 0) =>
  n.toLocaleString('es-MX', { style: 'currency', currency: 'USD', minimumFractionDigits: digits, maximumFractionDigits: digits })
