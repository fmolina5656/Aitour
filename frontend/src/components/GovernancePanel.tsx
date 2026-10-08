import { ACTOR_META } from '../agents'
import type { GovEvent, StageState } from '../types'

const ICON: Record<GovEvent['severity'], string> = { info: '✓', warning: '!', error: '⛔' }

/** Gobierno en vivo: cada chequeo de seguridad (pasa o bloquea) y cada llamada a modelos con su costo. */
export function GovernancePanel({ s }: { s: StageState }) {
  const tokens = s.spans.reduce((n, sp) => n + sp.input_tokens + sp.output_tokens, 0)
  return (
    <section className="block gov">
      <div className="block-head">
        <span>Gobierno</span>
        <span>Foundry</span>
      </div>
      <div className="stats">
        <div><b>{s.spans.length}</b><span>llamadas</span></div>
        <div><b>{tokens.toLocaleString('es-MX')}</b><span>tokens</span></div>
        <div><b>${s.sessionCost.toFixed(3)}</b><span>USD sesión</span></div>
      </div>
      <div className="gov-list">
        {s.governance.slice(0, 3).map((g, i) => (
          <div key={s.governance.length - i} className={`gov-event sev-${g.severity}`} title={g.detail}>
            <span className="gov-icon">{ICON[g.severity]}</span>
            <span className="gov-title">{g.title}</span>
          </div>
        ))}
      </div>
      <table className="table mono">
        <tbody>
          {s.spans.slice(0, 3).map((sp, i) => (
            <tr key={s.spans.length - i}>
              <td>{ACTOR_META[sp.agent]?.label}</td>
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
