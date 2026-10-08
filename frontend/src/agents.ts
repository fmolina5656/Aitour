import type { Lane } from './types'

export const LANES: Lane[] = ['visitante', 'arquitecto', 'financiero', 'riesgo', 'redactor']

export const LANE_META: Record<Lane, { label: string; role: string; thinking: string }> = {
  visitante: { label: 'Visitante', role: 'Cuenta el problema', thinking: '' },
  arquitecto: { label: 'Arquitecto', role: 'Diseña en Azure', thinking: 'está diseñando la solución' },
  financiero: { label: 'Financiero', role: 'Estima el costo', thinking: 'está revisando el costo' },
  riesgo: { label: 'Riesgo', role: 'Datos y regulación', thinking: 'está revisando datos y regulación' },
  redactor: { label: 'Redactor', role: 'Escribe el resumen', thinking: 'está escribiendo el one-pager' },
}

export const laneColor = (l: Lane) => `var(--who-${l})`

export const usd = (n: number) =>
  n.toLocaleString('es-MX', { style: 'currency', currency: 'USD', maximumFractionDigits: 0 })

/** Formato corto para las tarjetas: $4,972 */
export const money = (n: number) => `$${Math.round(n).toLocaleString('es-MX')}`
