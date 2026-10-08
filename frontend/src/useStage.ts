import { useEffect, useReducer } from 'react'
import type { AgentId, Cost, GovEvent, OnePager, Span, StageEvent, StageState } from './types'

export const initialState: StageState = {
  connected: false,
  mode: '',
  sessionId: null,
  phase: 'idle',
  brief: null,
  thinking: null,
  bubbles: {},
  feed: [],
  lastSpeaker: null,
  objection: null,
  spans: [],
  sessionCost: 0,
  governance: [],
  diagram: null,
  cost: null,
  costHistory: [],
  onepager: null,
  elapsed: 0,
  budget: 120,
}

type Action = StageEvent | { type: '__connected'; data: { value: boolean } }

export function reducer(s: StageState, ev: Action): StageState {
  const d = ev.data as Record<string, any>
  switch (ev.type) {
    case '__connected':
      return { ...s, connected: d.value }
    case 'hello':
      return { ...s, mode: d.mode }
    case 'session.started':
      return { ...initialState, connected: s.connected, mode: d.mode ?? s.mode, sessionId: d.session_id, phase: 'swarm', brief: d.brief }
    case 'session.reset':
      return { ...initialState, connected: s.connected, mode: s.mode }
    case 'session.ended':
      return { ...s, phase: 'done', thinking: null }
    case 'agent.thinking':
      return { ...s, thinking: d.agent as AgentId }
    case 'agent.delta': {
      const agent = d.agent as AgentId
      return { ...s, bubbles: { ...s.bubbles, [agent]: { agent, text: d.burbuja, final: false } } }
    }
    case 'agent.message': {
      const agent = d.agent as AgentId
      const objection = !!d.detalle?.objecion
      return {
        ...s,
        lastSpeaker: agent,
        bubbles: { ...s.bubbles, [agent]: { agent, text: d.burbuja, final: true, objection } },
        feed: [{ agent, text: d.burbuja, final: true, objection }, ...s.feed].slice(0, 4),
        objection: objection ? s.objection : agent === 'arquitecto' ? null : s.objection,
      }
    }
    case 'agent.objection':
      return { ...s, objection: d as StageState['objection'] }
    case 'trace.span':
      return { ...s, spans: [d as Span, ...s.spans].slice(0, 30), sessionCost: d.session_cost_usd }
    case 'governance.event':
      return { ...s, governance: [d as GovEvent, ...s.governance].slice(0, 12) }
    case 'artifact.diagram':
      return { ...s, diagram: { mermaid: d.mermaid, version: d.version, cambios: d.cambios } }
    case 'artifact.cost':
      return { ...s, cost: d as Cost, costHistory: [...s.costHistory, d.total_usd] }
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
