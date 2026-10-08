import { Color, QuadraticBezierCurve3, Vector3 } from 'three'
import type { AgentId, FlowNodeId } from '../types'

/** El problema del visitante vive en el núcleo; el equipo de agentes lo rodea. */
export const CORE = new Vector3(0, 0, -1.2)

// En arco alrededor del núcleo, en el orden en que hablan (izquierda → derecha)
export const AGENT_POS: Record<AgentId, Vector3> = {
  arquitecto: new Vector3(-6.2, 0, -0.8),
  financiero: new Vector3(-3.9, 0, -4.3),
  riesgo: new Vector3(0, 0, -8.2), // más al fondo: así asoma por encima de Glitch en vez de quedar detrás
  diagramador: new Vector3(3.9, 0, -4.3),
  redactor: new Vector3(6.2, 0, -0.8),
}

// Modo tablet: sin paneles alrededor, el arco se abre (más a lo ancho que en profundidad) para que respire
const TABLET_SPREAD = { x: 1.35, z: 1.15 }
const AGENT_POS_TABLET = Object.fromEntries(
  Object.entries(AGENT_POS).map(([id, p]) => [id, new Vector3(CORE.x + (p.x - CORE.x) * TABLET_SPREAD.x, p.y, CORE.z + (p.z - CORE.z) * TABLET_SPREAD.z)]),
) as Record<AgentId, Vector3>

export const agentPos = (id: AgentId, tablet = false) => (tablet ? AGENT_POS_TABLET : AGENT_POS)[id]

/** Visitante y one-pager son el mismo lugar: el problema entra y la solución sale del núcleo. */
export function posOf(id: FlowNodeId, tablet = false): Vector3 {
  return id === 'visitante' || id === 'onepager' ? CORE : agentPos(id, tablet)
}

/** Arco entre dos puntos. Las objeciones vuelan más alto, para que se distingan. */
export function arcBetween(from: FlowNodeId, to: FlowNodeId, objection: boolean, tablet = false): QuadraticBezierCurve3 {
  const a = posOf(from, tablet).clone()
  const b = posOf(to, tablet).clone()
  const mid = a.clone().add(b).multiplyScalar(0.5)
  const dist = a.distanceTo(b)
  mid.y += (objection ? 3.2 : 1.6) + dist * 0.18
  return new QuadraticBezierCurve3(a, mid, b)
}

/** Lee un color de los tokens de marca (branding.css) para usarlo en Three.js. */
export function cssColor(name: string, fallback = '#ffffff'): Color {
  const v = getComputedStyle(document.documentElement).getPropertyValue(name).trim()
  return new Color(v || fallback)
}

export const agentColor = (id: FlowNodeId) => cssColor(`--who-${id}`)
