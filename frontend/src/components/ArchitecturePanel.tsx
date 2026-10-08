import type { StageState } from '../types'

const ORDER = ['Datos', 'IA', 'Voz', 'Cómputo', 'Integración', 'Gobierno']

/**
 * Arquitectura propuesta, agrupada por capa. Marca lo que agregó o cambió el Arquitecto en la última versión:
 * así se ve cómo responde a las objeciones.
 */
export function ArchitecturePanel({ s }: { s: StageState }) {
  const cost = s.cost
  const prev = new Map((s.prevCost?.items ?? []).map((i) => [i.id, i.servicio]))
  const groups = ORDER.map((cat) => ({ cat, items: (cost?.items ?? []).filter((i) => i.categoria === cat) })).filter((g) => g.items.length)
  return (
    <section className="block">
      <div className="block-head">
        <span>Arquitectura propuesta</span>
        {cost && <span>v{cost.version}</span>}
      </div>
      {!cost && <div className="empty">Aparece cuando el Arquitecto proponga la solución.</div>}
      <div className="arch">
        {groups.map((g) => (
          <div key={g.cat} className="arch-col">
            <div className="arch-cat">{g.cat}</div>
            {g.items.map((i) => {
              const tag = !s.prevCost ? null : !prev.has(i.id) ? 'nuevo' : prev.get(i.id) !== i.servicio ? 'cambió' : null
              return (
                <div key={i.id} className={`arch-item ${tag ? 'is-new' : ''}`}>
                  {shortName(i.nombre)}
                  {tag && <span className="arch-tag">{tag}</span>}
                </div>
              )
            })}
          </div>
        ))}
      </div>
    </section>
  )
}

/** "Azure AI Search · Basic" → "AI Search"; "Foundry · GPT-5.4 mini" → "GPT-5.4 mini" */
function shortName(n: string) {
  const parts = n.split(' · ')
  const base = parts[0] === 'Foundry' ? parts[1] : parts[0]
  return base.replace(/^(Azure|Microsoft) /, '').split(' / ')[0]
}
