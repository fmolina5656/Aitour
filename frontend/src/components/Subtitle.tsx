import { useEffect, useState } from 'react'
import { ACTOR_META, nodeColor } from '../agents'
import type { AgentId, StageState, Turn } from '../types'

/** Modo tablet: en lugar del chat, una sola línea de subtítulo con quién habla y qué dice. */
export function Subtitle({ s }: { s: StageState }) {
  // cada respuesta terminada queda en pantalla el tiempo de leerla, aunque el siguiente agente ya haya arrancado
  const [holdIdx, setHoldIdx] = useState(-1)
  useEffect(() => {
    const t = s.turns.at(-1)
    if (!t || s.phase === 'idle') {
      setHoldIdx(-1)
      return
    }
    setHoldIdx(s.turns.length - 1)
    const id = window.setTimeout(() => setHoldIdx(-1), readMs(t.text))
    return () => window.clearTimeout(id)
  }, [s.turns.length])
  const held = holdIdx >= 0 && holdIdx < s.turns.length && s.live && !s.blocked ? s.turns[holdIdx] : null

  // mientras el agente piensa (sin texto todavía) va contando lo que hace, una frase cada pocos segundos
  const thinking = s.live && !s.live.text && !held ? s.live.agent : null
  const [beat, setBeat] = useState(0)
  useEffect(() => {
    setBeat(0)
    if (!thinking) return
    const id = window.setInterval(() => setBeat((b) => b + 1), 4000)
    return () => window.clearInterval(id)
  }, [thinking, s.turns.length])

  const line = held ? turnLine(held) : current(s, beat)
  if (!line) return null
  return (
    <div className="subtitle" style={{ ['--c' as string]: line.color }}>
      <div className="subtitle-who">
        {line.who}
        {line.action && <span className="subtitle-action">{line.action}</span>}
      </div>
      <div className="subtitle-text">
        <span>{line.text}</span>
      </div>
    </div>
  )
}

type Line = { who: string; action?: string; text: string; color: string }

function current(s: StageState, beat: number): Line | null {
  if (s.blocked) {
    return { who: 'Readymind', action: s.blocked.kind === 'jailbreak' ? 'Prompt Shields bloqueó la solicitud' : 'Fuera de alcance', text: s.blocked.reply, color: 'var(--brand-green)' }
  }
  if (s.phase === 'idle') {
    if (s.interview.agentLive) return { who: 'Recepcionista', text: s.interview.agentLive, color: 'var(--brand-green)' }
    const last = s.interview.lines.at(-1)
    if (!last) return null
    return last.who === 'recepcionista'
      ? { who: 'Recepcionista', text: last.text, color: 'var(--brand-green)' }
      : { who: 'Visitante', text: last.text, color: 'var(--who-visitante)' }
  }
  if (s.live) {
    const m = ACTOR_META[s.live.agent]
    const text = s.live.text || pick(narration(s, s.live.agent), beat)
    return { who: m.label, action: m.thinking, text, color: nodeColor(s.live.agent) }
  }
  const t = s.turns.at(-1)
  return t ? turnLine(t) : null
}

const turnLine = (t: Turn): Line => ({ who: ACTOR_META[t.actor].label, action: t.action, text: t.text, color: t.kind === 'object' ? 'var(--alert)' : nodeColor(t.actor) })

/** Tiempo de lectura cómodo a distancia: ~15 caracteres por segundo, entre 4 y 9 segundos. */
const readMs = (text: string) => Math.min(9000, Math.max(4000, 1500 + (text.length / 15) * 1000))

/** Avanza por las frases y se queda en la última si el modelo tarda. */
const pick = (lines: string[], beat: number) => lines[Math.min(beat, lines.length - 1)]

/** Lo que el agente "dice" mientras trabaja, según en qué punto de la discusión está. */
function narration(s: StageState, agent: AgentId): string[] {
  const industria = s.brief?.industria ? ` de ${s.brief.industria.toLowerCase()}` : ''
  const again = s.turns.some((t) => t.actor === agent)
  const prev = s.turns.at(-1)
  const objectedBy = prev?.kind === 'object' ? prev.actor : null

  switch (agent) {
    case 'arquitecto':
      if (objectedBy === 'financiero')
        return ['El Financiero tiene razón, sale caro. Déjame ver dónde recortar…', 'Busco un modelo más chico para el volumen y dejo el grande para las excepciones…', 'Rearmo la arquitectura con menos costo…']
      if (objectedBy === 'riesgo')
        return ['Buen punto de Riesgo. Reviso cómo proteger esos datos…', 'Agrego enmascaramiento de datos personales antes del modelo…', 'Ajusto la arquitectura para que cumpla…']
      if (again) return ['Tomo los comentarios del equipo y ajusto la propuesta…', 'Reviso que todo siga encajando…']
      return [`Leo tu problema${industria} y pienso qué necesitas…`, 'Busco en el catálogo de Azure los servicios que encajan…', 'Armo la primera versión de la arquitectura…']
    case 'financiero':
      if (again) return ['A ver, recalculo con los cambios del Arquitecto…', 'Comparo contra la versión anterior…', 'Reviso si ahora sí cierran los números…']
      return ['Saco la calculadora: ¿cuánto cuesta esto al mes?', 'Reviso los precios de Azure para tu volumen…', 'Veo qué parte del costo pesa más…']
    case 'riesgo':
      if (again) return ['Reviso de nuevo con los ajustes del Arquitecto…', 'Confirmo que los datos personales quedan protegidos…']
      return ['Reviso qué datos personales están en juego…', 'Cruzo la propuesta con la LFPDPPP y las normas mexicanas…', 'Veo si hace falta alguna protección extra…']
    case 'diagramador':
      return ['Dibujo cómo fluye la información en Azure…', 'Ordeno los pasos, de la entrada al resultado…', 'Le doy los últimos retoques al diagrama…']
    case 'redactor':
      return ['Junto todo lo que discutió el equipo…', 'Escribo el resumen ejecutivo en una página…', 'Pongo el costo, los riesgos y los próximos pasos…']
  }
}
