import { LANE_META } from '../agents'
import type { StageState } from '../types'

export function GovernancePanel({ s }: { s: StageState }) {
  const tokens = s.spans.reduce((n, sp) => n + sp.input_tokens + sp.output_tokens, 0)
  return (
    <section className="block">
      <div className="block-head">
        <span>Gobierno</span>
        <span className="muted">trazas OpenTelemetry</span>
      </div>
      <div className="stats">
        <div><b>{s.spans.length}</b><span>llamadas</span></div>
        <div><b>{tokens.toLocaleString('es-MX')}</b><span>tokens</span></div>
        <div><b>${s.sessionCost.toFixed(3)}</b><span>USD sesión</span></div>
      </div>
      {s.governance.slice(0, 2).map((g, i) => (
        <div key={i} className={`gov-event sev-${g.severity}`}>
          <b>{g.title}</b> — {g.detail}
        </div>
      ))}
      <table className="table mono">
        <tbody>
          {s.spans.slice(0, 5).map((sp, i) => (
            <tr key={s.spans.length - i}>
              <td>{LANE_META[sp.agent]?.label}</td>
              <td className="muted">{sp.model}</td>
              <td className="num">{(sp.latency_ms / 1000).toFixed(1)}s</td>
              <td className="num">{sp.input_tokens + sp.output_tokens}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </section>
  )
}
