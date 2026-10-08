import type { StageState } from '../types'

/**
 * Arquitectura en Azure, siempre a la vista: el diagrama aparece con la primera propuesta del Arquitecto, se
 * redibuja con cada ajuste (lo nuevo se marca en verde) y al final queda la versión del Diagramador.
 * El SVG lo arma el backend con texto escapado; el modelo nunca escribe el dibujo.
 */
export function ArchitecturePanel({ s }: { s: StageState }) {
  const d = s.diagram
  return (
    <section className="block block-grow">
      <div className="block-head">
        <span>Arquitectura en Azure</span>
        {d && (
          <span className={d.por === 'diagramador' ? 'arch-by' : ''}>
            {d.por === 'diagramador' ? `Diagramador · v${d.version}` : `v${d.version}`}
          </span>
        )}
      </div>
      {!d && <div className="empty">Aparece cuando el Arquitecto proponga la solución.</div>}
      {d && <div key={`${d.version}-${d.por}`} className="diagram" dangerouslySetInnerHTML={{ __html: d.svg }} />}
    </section>
  )
}
