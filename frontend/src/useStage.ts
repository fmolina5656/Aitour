import { useEffect, useReducer } from 'react'
import { money } from './agents'
import type { AgentId, Cost, GovEvent, OnePager, Span, StageEvent, StageState, Turn } from './types'

export const initialState: StageState = {
  connected: false,
  mode: '',
  sessionId: null,
  phase: 'idle',
  brief: null,
  turns: [],
  live: null,
  spans: [],
  sessionCost: 0,
  governance: [],
  diagram: null,
  cost: null,
  onepager: null,
  elapsed: 0,
  budget: 120,
}

type Action = StageEvent | { type: '__connected'; data: { value: boolean } }

/** Traduce el mensaje de un agente a un turno: qué hizo y qué produjo. */
function toTurn(s: StageState, agent: AgentId, text: string, d: Record<string, any>): Turn {
  const objected = !!d?.objecion
  switch (agent) {
    case 'arquitecto': {
      const first = !s.turns.some((t) => t.lane === 'arquitecto')
      const n = d?.componentes?.length
      return { lane: agent, kind: first ? 'propose' : 'adjust', action: first ? 'Propone arquitectura' : 'Ajusta la arquitectura', text, chip: n ? `${n} servicios` : undefined }
    }
    case 'financiero':
      return { lane: agent, kind: objected ? 'object' : 'approve', action: objected ? 'Objeta el costo' : 'Aprueba el costo', text, chip: s.cost ? `${money(s.cost.total_usd)}/mes` : undefined }
    case 'riesgo':
      return { lane: agent, kind: objected ? 'object' : 'approve', action: objected ? 'Señala un riesgo' : 'Valida cumplimiento', text, chip: d?.regulacion?.[0]?.norma?.split(' (')[0] }
    default:
      return { lane: agent, kind: 'write', action: 'Redacta el one-pager', text, chip: 'Resumen listo' }
  }
}

export function reducer(s: StageState, ev: Action): StageState {
  const d = ev.data as Record<string, any>
  switch (ev.type) {
    case '__connected':
      return { ...s, connected: d.value }
    case 'hello':
      return { ...s, mode: d.mode }
    case 'session.started': {
      const brief = d.brief ?? {}
      const turns: Turn[] = [{ lane: 'visitante', kind: 'brief', action: 'Cuenta su problema', text: brief.problema ?? '', chip: brief.industria }]
      return { ...initialState, connected: s.connected, mode: d.mode ?? s.mode, sessionId: d.session_id, phase: 'swarm', brief, turns }
    }
    case 'session.reset':
      return { ...initialState, connected: s.connected, mode: s.mode }
    case 'session.ended':
      return { ...s, phase: 'done', live: null }
    case 'agent.thinking':
      return { ...s, live: { agent: d.agent, text: '' } }
    case 'agent.delta':
      return { ...s, live: { agent: d.agent, text: d.burbuja } }
    case 'agent.message':
      return { ...s, live: null, turns: [...s.turns, toTurn(s, d.agent, d.burbuja, d.detalle ?? {})] }
    case 'trace.span':
      return { ...s, spans: [d as Span, ...s.spans].slice(0, 30), sessionCost: d.session_cost_usd }
    case 'governance.event':
      return { ...s, governance: [d as GovEvent, ...s.governance].slice(0, 12) }
    case 'artifact.diagram':
      return { ...s, diagram: { mermaid: d.mermaid, version: d.version } }
    case 'artifact.cost': {
      // el costo llega justo después del turno del Arquitecto: se suma a su tarjeta
      const turns = [...s.turns]
      const last = turns[turns.length - 1]
      if (last?.lane === 'arquitecto') {
        const delta = s.cost ? d.total_usd - s.cost.total_usd : 0
        const chip = delta ? `${delta < 0 ? '−' : '+'}${money(Math.abs(delta))}/mes` : last.chip
        turns[turns.length - 1] = { ...last, chip: `v${d.version} · ${chip}` }
      }
      return { ...s, cost: d as Cost, turns }
    }
    case 'artifact.onepager':
      return { ...s, onepager: d as OnePager }
    case 'clock':
      return { ...s, elapsed: d.elapsed_s, budget: d.budget_s }
    default:
      return s
  }
}

/** Conexión al bus del backend con reconexión automática. */
export function useStage() {
  const [state, dispatch] = useReducer(reducer, initialState)
  useEffect(() => {
    let ws: WebSocket | null = null
    let retry: number | undefined
    let alive = true
    const connect = () => {
      const proto = location.protocol === 'https:' ? 'wss' : 'ws'
      ws = new WebSocket(`${proto}://${location.host}/ws/stage`)
      ws.onopen = () => dispatch({ type: '__connected', data: { value: true } })
      ws.onmessage = (m) => dispatch(JSON.parse(m.data))
      ws.onclose = () => {
        dispatch({ type: '__connected', data: { value: false } })
        if (alive) retry = window.setTimeout(connect, 1000)
      }
    }
    connect()
    return () => {
      alive = false
      window.clearTimeout(retry)
      ws?.close()
    }
  }, [])
  return state
}

export const api = {
  reset: () => fetch('/api/reset', { method: 'POST' }),
  startText: (body: Record<string, string>) =>
    fetch('/api/session/text', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(body) }),
}
