import { motion } from 'framer-motion'
import { usd } from '../agents'
import type { OnePager } from '../types'

/** Cierre de la sesión. En la Fase 4 se agrega el QR para dejar los datos y recibir el PDF. */
export function OnePagerOverlay({ op, onClose }: { op: OnePager; onClose: () => void }) {
  const o = op.onepager
  return (
    <motion.div className="overlay" initial={{ opacity: 0 }} animate={{ opacity: 1 }} onClick={onClose}>
      <motion.div className="onepager" initial={{ y: 40, scale: 0.97 }} animate={{ y: 0, scale: 1 }} onClick={(e) => e.stopPropagation()}>
        <div className="op-kicker">One-pager ejecutivo · generado en vivo por 4 agentes</div>
        <h1>{o.titulo}</h1>
        <div className="op-grid">
          <div>
            <h3>El problema</h3>
            <p>{o.problema}</p>
            <h3>La solución</h3>
            <p>{o.solucion}</p>
          </div>
          <div>
            <h3>Beneficios</h3>
            <ul>{o.beneficios.map((b) => <li key={b}>{b}</li>)}</ul>
            <h3>Riesgos y mitigaciones</h3>
            <ul>{o.riesgos_y_mitigaciones.map((b) => <li key={b}>{b}</li>)}</ul>
          </div>
          <div className="op-side">
            <div className="op-cost">{op.costo ? usd(op.costo.total_usd) : '—'}<span>/ mes estimado</span></div>
            <h3>Siguientes pasos</h3>
            <ol>{o.siguientes_pasos.map((b) => <li key={b}>{b}</li>)}</ol>
            <div className="qr-placeholder">QR · Fase 4</div>
          </div>
        </div>
        {op.costo && <div className="disclaimer">⚠ {op.costo.disclaimer}</div>}
      </motion.div>
    </motion.div>
  )
}
