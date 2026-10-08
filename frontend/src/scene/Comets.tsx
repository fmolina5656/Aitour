import { useFrame } from '@react-three/fiber'
import { useLayoutEffect, useMemo, useRef } from 'react'
import { Color, MathUtils, TubeGeometry, type InstancedMesh, type MeshBasicMaterial, Object3D } from 'three'
import type { Handoff } from '../types'
import { arcBetween, cssColor } from './layout'

const ease = (t: number) => (t < 0.5 ? 4 * t * t * t : 1 - Math.pow(-2 * t + 2, 3) / 2)

/** Cables persistentes (un arco por cada par que conversó) + cometas por cada traspaso reciente. */
export function Links({ handoffs }: { handoffs: Handoff[] }) {
  const accent = useMemo(() => cssColor('--accent'), [])
  const alert = useMemo(() => cssColor('--alert'), [])
  const green = useMemo(() => cssColor('--brand-green'), [])

  const pairs = useMemo(() => {
    const m = new Map<string, Handoff & { last: number }>()
    for (const h of handoffs) {
      const k = `${h.from}->${h.to}`
      const prev = m.get(k)
      m.set(k, { ...h, objection: (prev?.objection ?? false) || h.objection, last: h.seq })
    }
    return [...m.values()]
  }, [handoffs])

  const lastSeq = handoffs.length ? handoffs[handoffs.length - 1].seq : 0
  const recent = handoffs.filter((h) => h.seq > lastSeq - 2)

  return (
    <>
      {pairs.map((p) => (
        <Cable key={`${p.from}->${p.to}`} h={p} color={p.objection ? alert : accent} fresh={p.last === lastSeq} />
      ))}
      {recent.map((h) => (
        <Comet key={h.seq} h={h} head={h.objection ? alert : accent} tail={h.objection ? alert : green} />
      ))}
    </>
  )
}

function Cable({ h, color, fresh }: { h: Handoff; color: Color; fresh: boolean }) {
  const geo = useMemo(() => new TubeGeometry(arcBetween(h.from, h.to, h.objection), 80, h.objection ? 0.035 : 0.025, 8, false), [h.from, h.to, h.objection])
  const mat = useRef<MeshBasicMaterial>(null)
  const grow = useRef(0)
  useFrame((_, dt) => {
    grow.current = Math.min(grow.current + dt / 1.2, 1)
    if (mat.current) mat.current.opacity = MathUtils.damp(mat.current.opacity, (fresh ? 0.75 : 0.28) * grow.current, 3, dt)
  })
  return (
    <mesh geometry={geo}>
      <meshBasicMaterial ref={mat} color={color} transparent opacity={0} toneMapped={false} depthWrite={false} />
    </mesh>
  )
}

const TAIL = 26
const dummy = new Object3D()

/**
 * Cometa: cabeza brillante + cola de partículas muestreadas sobre la MISMA curva (sin artefactos).
 * Un solo InstancedMesh por cometa.
 */
function Comet({ h, head, tail }: { h: Handoff; head: Color; tail: Color }) {
  const curve = useMemo(() => arcBetween(h.from, h.to, h.objection), [h.from, h.to, h.objection])
  const mesh = useRef<InstancedMesh>(null)
  const t = useRef(0)
  const size = h.objection ? 0.2 : 0.15
  const dur = h.objection ? 1.7 : 1.35
  // Cola con el degradado de marca: cabeza azul → cola verde (como "READY"). Valores > 1 para el bloom.
  useLayoutEffect(() => {
    const m = mesh.current
    if (!m) return
    const c = new Color()
    for (let i = 0; i < TAIL; i++) {
      c.copy(head).lerp(tail, i / TAIL).multiplyScalar(3)
      m.setColorAt(i, c)
    }
    if (m.instanceColor) m.instanceColor.needsUpdate = true
  }, [head, tail])
  useFrame((_, dt) => {
    t.current = Math.min(t.current + dt / dur, 1.6)
    const m = mesh.current
    if (!m) return
    for (let i = 0; i < TAIL; i++) {
      const k = i / TAIL
      const tt = t.current - k * 0.28
      const visible = tt > 0 && tt < 1
      const p = curve.getPoint(ease(Math.min(Math.max(tt, 0), 1)))
      dummy.position.copy(p)
      dummy.scale.setScalar(visible ? size * (1 - k) ** 1.4 : 0)
      dummy.updateMatrix()
      m.setMatrixAt(i, dummy.matrix)
    }
    m.instanceMatrix.needsUpdate = true
  })
  return (
    <instancedMesh ref={mesh} args={[undefined, undefined, TAIL]} frustumCulled={false}>
      <sphereGeometry args={[1, 12, 12]} />
      <meshBasicMaterial toneMapped={false} transparent opacity={0.9} depthWrite={false} />
    </instancedMesh>
  )
}
