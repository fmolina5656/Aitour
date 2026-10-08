import { AnimatePresence, motion } from 'framer-motion'
import { AGENTS, agentColor } from '../agents'
import type { StageState } from '../types'

export function GovernancePanel({ s }: { s: StageState }) {
  const tokens = s.spans.reduce((n, sp) => n + sp.input_tokens + sp.output_tokens, 0)
  return (
    <aside className="panel gov">
      <div className="panel-title">Panel de gobierno</div>
      <div className="kpis">
        <Kpi label="Costo de esta sesión" value={`US$ ${s.sessionCost.toFixed(4)}`} />
        <Kpi label="Llamadas" value={String(s.spans.length)} />
        <Kpi label="Tokens" value={tokens.toLocaleString('es-MX')} />
      </div>

      <AnimatePresence>
        {s.governance.slice(0, 3).map((g, i) => (
          <motion.div key={`${g.title}-${i}`} className={`gov-alert sev-${g.severity}`} initial={{ opacity: 0, x: 40 }} animate={{ opacity: 1, x: 0 }}>
            <div className="gov-alert-title">🛡 {g.title}</div>
            <div className="gov-alert-detail">{g.detail}</div>
          </motion.div>
        ))}
      </AnimatePresence>

      <div className="panel-subtitle">Trazas en vivo · OpenTelemetry → Foundry</div>
      <div className="spans">
        <AnimatePresence initial={false}>
          {s.spans.map((sp, i) => (
            <motion.div key={s.spans.length - i} className="span" initial={{ opacity: 0, y: -12 }} animate={{ opacity: 1, y: 0 }}>
              <span className="span-dot" style={{ background: agentColor(sp.agent) }} />
              <span className="span-agent">{AGENTS[sp.agent]?.label ?? sp.agent}</span>
              <span className="span-model">{sp.model}</span>
              <span className="span-num">{(sp.input_tokens + sp.output_tokens).toLocaleString('es-MX')} tok</span>
              <span className="span-num">{(sp.latency_ms / 1000).toFixed(1)} s</span>
              <span className="span-num">${sp.cost_usd.toFixed(4)}</span>
            </motion.div>
          ))}
        </AnimatePresence>
        {s.spans.length === 0 && <div className="muted">Las llamadas a modelos aparecerán aquí.</div>}
      </div>
    </aside>
  )
}

function Kpi({ label, value }: { label: string; value: string }) {
  return (
    <div className="kpi">
      <div className="kpi-value">{value}</div>
      <div className="kpi-label">{label}</div>
    </div>
  )
}
