import { usd } from '../agents'
import type { OnePager } from '../types'

/** Cierre de la sesión: el one-pager y el QR para dejar los datos y recibir el PDF. */
export function OnePagerOverlay({ op, qrUrl, onClose }: { op: OnePager; qrUrl?: string; onClose: () => void }) {
  const o = op.onepager
  return (
    <div className="overlay" onClick={onClose}>
      <article className="onepager" onClick={(e) => e.stopPropagation()}>
        <div className="op-kicker">One-pager ejecutivo</div>
        <h1>{o.titulo}</h1>
        <div className="op-grid">
          <div>
            <h3>Problema</h3>
            <p>{o.problema}</p>
            <h3>Solución</h3>
            <p>{o.solucion}</p>
          </div>
          <div>
            <h3>Beneficios</h3>
            <ul>{o.beneficios.map((b) => <li key={b}>{b}</li>)}</ul>
            <h3>Riesgos y mitigaciones</h3>
            <ul>{o.riesgos_y_mitigaciones.map((b) => <li key={b}>{b}</li>)}</ul>
          </div>
          <div>
            <h3>Costo estimado</h3>
            <p className="op-cost">{op.costo ? `${usd(op.costo.total_usd)} /mes` : '—'}</p>
            <h3>Siguientes pasos</h3>
            <ol>{o.siguientes_pasos.map((b) => <li key={b}>{b}</li>)}</ol>
            {qrUrl ? <img className="op-qr" src={qrUrl} alt="QR" /> : null}
            {qrUrl && <div className="muted">Escanea para recibirlo en PDF</div>}
          </div>
        </div>
        {op.costo && <div className="fine">{op.costo.disclaimer}</div>}
      </article>
    </div>
  )
}
