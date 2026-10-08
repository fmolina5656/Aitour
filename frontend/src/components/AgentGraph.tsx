import { AnimatePresence, motion } from 'framer-motion'
import { AGENTS, AGENT_ORDER, agentColor } from '../agents'
import type { AgentId, Bubble, StageState } from '../types'

// Centro del "spotlight" (en % del área del grafo)
const HUB = { x: 50, y: 58 }

export function AgentGraph({ s }: { s: StageState }) {
  const active = s.thinking
  const obj = s.objection
  const live = active ? s.bubbles[active] : undefined
  // Burbuja principal: lo que está diciendo el agente activo; si no, el último mensaje.
  const current: Bubble | undefined = active ? (live && !live.final ? live : undefined) : s.feed[0]
  const previous = active ? s.feed[0] : s.feed[1]
  return (
    <div className="graph">
      <div className="problem-strip">
        <span className="problem-label">Tu problema</span>
        <span className="problem-text">{s.brief?.problema ?? 'Esperando visitante…'}</span>
      </div>

      <svg className="graph-svg" viewBox="0 0 100 100" preserveAspectRatio="none">
        {AGENT_ORDER.map((a) => (
          <line
            key={a}
            x1={HUB.x}
            y1={HUB.y}
            x2={AGENTS[a].x}
            y2={AGENTS[a].y}
            className={`edge ${active === a ? 'edge-active' : ''}`}
            style={{ stroke: active === a ? agentColor(a) : undefined }}
            vectorEffect="non-scaling-stroke"
          />
        ))}
        {obj && (
          <line
            x1={AGENTS[obj.de].x}
            y1={AGENTS[obj.de].y}
            x2={AGENTS[obj.para].x}
            y2={AGENTS[obj.para].y}
            className="edge-objection"
            vectorEffect="non-scaling-stroke"
          />
        )}
      </svg>

      <div className="spotlight" style={{ left: `${HUB.x}%`, top: `${HUB.y}%` }}>
        <AnimatePresence>
          {obj && (
            <motion.div key={`${obj.de}-${obj.motivo}`} className="objection-tag" initial={{ scale: 0.6, opacity: 0 }} animate={{ scale: 1, opacity: 1 }} exit={{ opacity: 0 }}>
              ⚡ OBJECIÓN · {AGENTS[obj.de].label} → {AGENTS[obj.para].label}
            </motion.div>
          )}
        </AnimatePresence>
        <AnimatePresence mode="popLayout">
          {previous && (
            <motion.div key={`p-${previous.agent}-${previous.text}`} layout className="bubble bubble-prev" style={{ ['--c' as string]: agentColor(previous.agent) }} initial={{ opacity: 0 }} animate={{ opacity: 0.5 }} exit={{ opacity: 0 }}>
              <BubbleHead b={previous} />
              {previous.text}
            </motion.div>
          )}
          {(current || active) && (
            <motion.div
              key={`c-${active ?? current?.agent}-${current?.final ? current.text : 'live'}`}
              layout
              className={`bubble bubble-main ${current?.objection ? 'bubble-objection' : ''}`}
              style={{ ['--c' as string]: agentColor((active ?? current?.agent) as AgentId) }}
              initial={{ opacity: 0, y: 20, scale: 0.98 }}
              animate={{ opacity: 1, y: 0, scale: 1 }}
              exit={{ opacity: 0 }}
            >
              <BubbleHead b={current ?? { agent: active as AgentId, text: '', final: false }} live={!!active} />
              {current?.text ? current.text : <span className="dots">pensando</span>}
            </motion.div>
          )}
        </AnimatePresence>
        {!current && !active && !previous && <div className="spotlight-empty">Aquí conversan los agentes</div>}
      </div>

      {AGENT_ORDER.map((a) => (
        <AgentNode key={a} id={a} s={s} />
      ))}
    </div>
  )
}

function BubbleHead({ b, live }: { b: Bubble; live?: boolean }) {
  return (
    <div className="bubble-head">
      {AGENTS[b.agent].label}
      {b.objection && <span className="tag-obj">objeción</span>}
      {live && <span className="tag-live">en vivo</span>}
    </div>
  )
}

function AgentNode({ id, s }: { id: AgentId; s: StageState }) {
  const meta = AGENTS[id]
  const thinking = s.thinking === id
  const spoke = !!s.bubbles[id]
  return (
    <div className="agent" style={{ left: `${meta.x}%`, top: `${meta.y}%`, ['--c' as string]: agentColor(id) }}>
      <motion.div
        className={`agent-orb ${thinking ? 'is-active' : ''} ${spoke ? 'has-spoken' : ''}`}
        animate={thinking ? { scale: [1, 1.08, 1] } : { scale: 1 }}
        transition={thinking ? { repeat: Infinity, duration: 1.4 } : {}}
      >
        <span className="agent-icon">{meta.icon}</span>
      </motion.div>
      <div className="agent-label">
        <div className="agent-name">{meta.label}</div>
        <div className="agent-role">{meta.role}</div>
      </div>
    </div>
  )
}
