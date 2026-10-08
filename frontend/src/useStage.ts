import { useEffect, useReducer } from 'react'
import { money } from './agents'
import type { Actor, AgentId, Cost, FlowNodeId, GovEvent, Handoff, OnePager, Span, StageEvent, StageState, Turn } from './types'

export const initialState: StageState = {
  connected: false,
  mode: '',
  models: {},
  sessionId: null,
  phase: 'idle',
  brief: null,
  turns: [],
  live: null,
  lastActor: null,
  status: {},
  chips: {},
  handoffs: [],
  subPulses: {},
  spans: [],
  sessionCost: 0,
  governance: [],
  diagram: null,
  cost: null,
  prevCost: null,
  onepager: null,
  blocked: null,
  interview: { active: false, lines: [], agentLive: '', proposed: null },
  elapsed: 0,
  budget: 120,
}

type Action = StageEvent | { type: '__connected'; data: { value: boolean } }

/** Traduce el mensaje de un agente a un turno: qué hizo y qué produjo. */
function toTurn(s: StageState, agent: AgentId, text: string, d: Record<string, any>): Turn {
  const objected = !!d?.objecion
  switch (agent) {
    case 'arquitecto': {
      const first = !s.turns.some((t) => t.actor === 'arquitecto')
      const n = d?.componentes?.length
      return { actor: agent, kind: first ? 'propose' : 'adjust', action: first ? 'Propone arquitectura' : 'Ajusta la arquitectura', text, chip: n ? `${n} servicios` : undefined }
    }
    case 'financiero':
      return { actor: agent, kind: objected ? 'object' : 'approve', action: objected ? 'Objeta el costo' : 'Aprueba el costo', text, chip: s.cost ? `${money(s.cost.total_usd)}/mes` : undefined }
    case 'riesgo':
      return { actor: agent, kind: objected ? 'object' : 'approve', action: objected ? 'Señala un riesgo' : 'Valida cumplimiento', text, chip: d?.regulacion?.[0]?.norma?.split(' (')[0] }
    default:
      return { actor: agent, kind: 'write', action: 'Redacta el one-pager', text, chip: 'Listo' }
  }
}

function handoff(s: StageState, from: FlowNodeId, to: FlowNodeId): Handoff[] {
  const lastTurn = [...s.turns].reverse().find((t) => t.actor === from)
  return [...s.handoffs, { from, to, objection: lastTurn?.kind === 'object', seq: s.handoffs.length + 1 }]
}

const pulse = (s: StageState, key: string) => ({ ...s.subPulses, [key]: (s.subPulses[key] ?? 0) + 1 })

export function reducer(s: StageState, ev: Action): StageState {
  const d = ev.data as Record<string, any>
  switch (ev.type) {
    case '__connected':
      return { ...s, connected: d.value }
    case 'hello':
      return { ...s, mode: d.mode, models: d.models ?? {} }
    case 'session.started': {
      const brief = d.brief ?? {}
      return {
        ...initialState,
        connected: s.connected,
        models: s.models,
        interview: { ...s.interview, active: false, proposed: null, agentLive: '' },
        mode: d.mode ?? s.mode,
        sessionId: d.session_id,
        phase: 'swarm',
        brief,
        lastActor: 'visitante',
        status: { visitante: 'done' },
        chips: { visitante: brief.industria },
        turns: [{ actor: 'visitante', kind: 'brief', action: 'Cuenta su problema', text: brief.problema ?? '', chip: brief.industria }],
      }
    }
    case 'session.reset':
      return { ...initialState, connected: s.connected, mode: s.mode, models: s.models }
    case 'session.ended':
      return { ...s, phase: 'done', live: null }
    case 'agent.thinking': {
      const agent = d.agent as AgentId
      const from = s.lastActor ?? 'visitante'
      return {
        ...s,
        live: { agent, text: '' },
        status: { ...s.status, [agent]: 'running' },
        handoffs: from !== agent ? handoff(s, from, agent) : s.handoffs,
      }
    }
    case 'agent.delta':
      return { ...s, live: { agent: d.agent, text: d.burbuja } }
    case 'agent.message': {
      const agent = d.agent as AgentId
      const turn = toTurn(s, agent, d.burbuja, d.detalle ?? {})
      return {
        ...s,
        live: null,
        lastActor: agent,
        turns: [...s.turns, turn],
        status: { ...s.status, [agent]: turn.kind === 'object' ? 'objected' : 'done' },
        chips: turn.chip ? { ...s.chips, [agent]: turn.chip } : s.chips,
      }
    }
    case 'trace.span':
      return { ...s, spans: [d as Span, ...s.spans].slice(0, 30), sessionCost: d.session_cost_usd, subPulses: pulse(s, `model-${d.agent}`) }
    case 'voice.started':
      return { ...initialState, connected: s.connected, mode: s.mode, models: s.models, interview: { active: true, lines: [], agentLive: '', proposed: null } }
    case 'voice.agent':
      return d.final
        ? { ...s, interview: { ...s.interview, agentLive: '', lines: [...s.interview.lines, { who: 'recepcionista', text: d.text }] } }
        : { ...s, interview: { ...s.interview, agentLive: d.text } }
    case 'voice.user':
      return { ...s, interview: { ...s.interview, lines: [...s.interview.lines, { who: 'visitante', text: d.text }] } }
    case 'brief.proposed':
      return { ...s, interview: { ...s.interview, proposed: d.brief } }
    case 'brief.confirmed':
      return { ...s, interview: { ...s.interview, proposed: null } }
    case 'voice.ended':
      return { ...s, interview: { ...s.interview, active: false, proposed: null, agentLive: '' } }
    case 'guard.blocked':
      return { ...s, blocked: { kind: d.kind, reply: d.reply }, live: null }
    case 'governance.event':
      return { ...s, governance: [d as GovEvent, ...s.governance].slice(0, 12) }
    case 'artifact.diagram':
      return { ...s, diagram: { mermaid: d.mermaid, version: d.version }, subPulses: pulse(s, 'tool-catalogo') }
    case 'artifact.cost': {
      // el costo llega justo después del turno del Arquitecto: se resume en su nodo
      const delta = s.cost ? d.total_usd - s.cost.total_usd : 0
      const chip = delta ? `v${d.version} · ${delta < 0 ? '−' : '+'}${money(Math.abs(delta))}` : `v${d.version} · ${money(d.total_usd)}`
      return { ...s, cost: d as Cost, prevCost: s.cost, chips: { ...s.chips, arquitecto: chip }, subPulses: pulse(s, 'tool-calc') }
    }
    case 'artifact.risk':
      return { ...s, subPulses: pulse(s, 'tool-normas') }
    case 'artifact.onepager':
      return {
        ...s,
        onepager: d as OnePager,
        status: { ...s.status, onepager: 'done' },
        chips: { ...s.chips, onepager: s.cost ? `${money(s.cost.total_usd)}/mes` : 'Listo' },
        handoffs: handoff(s, (s.lastActor ?? 'redactor') as Actor, 'onepager'),
      }
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
