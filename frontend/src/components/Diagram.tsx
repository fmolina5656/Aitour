import mermaid from 'mermaid'
import { useEffect, useRef, useState } from 'react'

let initialized = false
function init() {
  if (initialized) return
  const css = getComputedStyle(document.documentElement)
  const v = (name: string) => css.getPropertyValue(name).trim()
  mermaid.initialize({
    startOnLoad: false,
    theme: 'base',
    securityLevel: 'strict',
    themeVariables: {
      darkMode: true,
      background: 'transparent',
      fontFamily: v('--font'),
      fontSize: '16px',
      primaryColor: v('--surface'),
      primaryTextColor: v('--text'),
      primaryBorderColor: v('--line-strong'),
      lineColor: v('--text-3'),
      edgeLabelBackground: v('--bg'),
    },
    flowchart: { curve: 'basis', padding: 8, nodeSpacing: 18, rankSpacing: 26, useMaxWidth: true },
  })
  initialized = true
}

// El backend marca cada nodo con su categoría; aquí todas se ven neutras y sobrias.
const CLASS_DEFS = ['ia', 'datos', 'comp', 'integ', 'gob'].map((c) => `\n  classDef ${c} fill:#15181d,stroke:#3a414c,stroke-width:1px,color:#eceef2`).join('')

export function Diagram({ code, version }: { code: string | null; version?: number }) {
  const ref = useRef<HTMLDivElement>(null)
  const [error, setError] = useState(false)
  useEffect(() => {
    if (!code || !ref.current) return
    init()
    let cancelled = false
    mermaid
      .render(`mm-${Date.now()}`, code.replace(/^flowchart LR/, 'flowchart TD') + CLASS_DEFS)
      .then(({ svg }) => {
        if (!cancelled && ref.current) {
          ref.current.innerHTML = svg
          setError(false)
        }
      })
      .catch(() => !cancelled && setError(true))
    return () => {
      cancelled = true
    }
  }, [code])

  return (
    <section className="block block-grow">
      <div className="block-head">
        <span>Arquitectura</span>
        {version && <span className="muted">v{version}</span>}
      </div>
      {!code && <div className="empty">Aparece cuando el Arquitecto proponga la solución.</div>}
      {error && <div className="empty">No se pudo dibujar el diagrama.</div>}
      <div ref={ref} className="diagram" />
    </section>
  )
}
