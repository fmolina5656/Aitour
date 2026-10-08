import { motion } from 'framer-motion'
import { usd } from '../agents'
import type { StageState } from '../types'

export function CostPanel({ s }: { s: StageState }) {
  const cost = s.cost
  const max = Math.max(...(cost?.items.map((i) => i.costo_usd) ?? [1]), 1)
  const prev = s.costHistory.length > 1 ? s.costHistory[s.costHistory.length - 2] : null
  return (
    <section className="panel cost">
      <div className="panel-title">Costo mensual estimado {cost ? <span className="badge">v{cost.version}</span> : null}</div>
      {!cost && <div className="muted big">El Financiero calculará el costo aquí…</div>}
      {cost && (
        <>
          <div className="cost-total">
            <motion.span key={cost.total_usd} initial={{ scale: 1.25, color: 'var(--rm-primary-2)' }} animate={{ scale: 1, color: 'var(--rm-text)' }}>
              {usd(cost.total_usd)}
            </motion.span>
            <span className="cost-unit">/ mes</span>
            {prev !== null && prev !== cost.total_usd && (
              <span className={`cost-delta ${cost.total_usd < prev ? 'down' : 'up'}`}>
                {cost.total_usd < prev ? '▼' : '▲'} {usd(Math.abs(cost.total_usd - prev))}
              </span>
            )}
          </div>
          <div className="cost-items">
            {[...cost.items]
              .sort((a, b) => b.costo_usd - a.costo_usd)
              .slice(0, 6)
              .map((i) => (
                <div key={i.id} className="cost-row" title={i.supuesto}>
                  <span className="cost-name">
                    {i.nombre} {i.premium && <span className="premium">premium</span>}
                  </span>
                  <span className="cost-bar">
                    <motion.span className="cost-bar-fill" animate={{ width: `${(i.costo_usd / max) * 100}%` }} />
                  </span>
                  <span className="cost-val">{usd(i.costo_usd)}</span>
                </div>
              ))}
          </div>
          <div className="disclaimer">⚠ {cost.disclaimer}</div>
        </>
      )}
    </section>
  )
}
