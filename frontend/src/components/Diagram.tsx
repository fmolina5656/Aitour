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
      fontFamily: v('--rm-font'),
      fontSize: '22px',
      primaryColor: v('--rm-surface-2'),
      primaryTextColor: v('--rm-text'),
      primaryBorderColor: v('--rm-primary'),
      lineColor: v('--rm-text-dim'),
      edgeLabelBackground: v('--rm-bg-2'),
    },
    flowchart: { curve: 'basis', padding: 12, nodeSpacing: 30, rankSpacing: 50 },
  })
  initialized = true
}

const CLASS_DEFS = `
  classDef ia fill:#1d2f6b,stroke:#2f6bff,stroke-width:2px,color:#fff
  classDef datos fill:#173a3a,stroke:#2bd98a,stroke-width:2px,color:#fff
  classDef comp fill:#2a2350,stroke:#7a5cff,stroke-width:2px,color:#fff
  classDef integ fill:#3a2a1a,stroke:#ffb547,stroke-width:2px,color:#fff
  classDef gob fill:#3a1a2a,stroke:#ff5470,stroke-width:2px,color:#fff`

export function Diagram({ code, version, cambios }: { code: string | null; version?: number; cambios?: string | null }) {
  const ref = useRef<HTMLDivElement>(null)
  const [error, setError] = useState(false)
  useEffect(() => {
    if (!code || !ref.current) return
    init()
    let cancelled = false
    mermaid
      .render(`mm-${Date.now()}`, code + CLASS_DEFS)
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
    <section className="panel diagram">
      <div className="panel-title">
        Arquitectura propuesta {version ? <span className="badge">v{version}</span> : null}
      </div>
      {cambios && <div className="cambios">↻ {cambios}</div>}
      {!code && <div className="muted big">El Arquitecto dibujará la solución aquí…</div>}
      {error && <div className="muted">No se pudo renderizar el diagrama.</div>}
      <div ref={ref} className="diagram-svg" />
    </section>
  )
}
