import { usd } from '../agents'
import type { StageState } from '../types'

export function CostPanel({ s }: { s: StageState }) {
  const cost = s.cost
  return (
    <section className="block">
      <div className="block-head">
        <span>Costo mensual estimado</span>
        {cost && <span className="muted">v{cost.version}</span>}
      </div>
      {!cost ? (
        <div className="empty">Aparece cuando el Arquitecto proponga la solución.</div>
      ) : (
        <>
          <div className="cost-total">{usd(cost.total_usd)}<span className="muted"> /mes</span></div>
          <table className="table">
            <tbody>
              {[...cost.items]
                .sort((a, b) => b.costo_usd - a.costo_usd)
                .slice(0, 4)
                .map((i) => (
                  <tr key={i.id}>
                    <td>{i.nombre}</td>
                    <td className="num">{usd(i.costo_usd)}</td>
                  </tr>
                ))}
            </tbody>
          </table>
          <div className="fine">Estimación referencial. No constituye una cotización.</div>
        </>
      )}
    </section>
  )
}
