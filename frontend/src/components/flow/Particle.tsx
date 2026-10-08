import { useEffect, useRef } from 'react'

/** Bolita que recorre un cable una vez (requestAnimationFrame + getPointAtLength: fluido y preciso). */
export function Particle({ d, color, duration = 1100, delay = 0 }: { d: string; color: string; duration?: number; delay?: number }) {
  const pathRef = useRef<SVGPathElement>(null)
  const dotRef = useRef<SVGGElement>(null)
  useEffect(() => {
    const path = pathRef.current
    const dot = dotRef.current
    if (!path || !dot) return
    const len = path.getTotalLength()
    let raf = 0
    const start = performance.now() + delay
    const ease = (t: number) => (t < 0.5 ? 2 * t * t : 1 - Math.pow(-2 * t + 2, 2) / 2)
    const tick = (now: number) => {
      const t = Math.min(Math.max((now - start) / duration, 0), 1)
      const p = path.getPointAtLength(ease(t) * len)
      dot.setAttribute('transform', `translate(${p.x},${p.y})`)
      dot.style.opacity = t <= 0 || t >= 1 ? '0' : '1'
      if (t < 1) raf = requestAnimationFrame(tick)
    }
    raf = requestAnimationFrame(tick)
    return () => cancelAnimationFrame(raf)
  }, [d, duration, delay])
  return (
    <>
      <path ref={pathRef} d={d} fill="none" stroke="none" />
      <g ref={dotRef} style={{ opacity: 0 }}>
        <circle r={14} fill={color} opacity={0.18} />
        <circle r={7} fill={color} />
      </g>
    </>
  )
}
