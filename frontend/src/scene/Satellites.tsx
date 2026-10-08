import { Html, Line } from '@react-three/drei'
import { useFrame } from '@react-three/fiber'
import { useRef } from 'react'
import { MathUtils, type Color, type Group, type Mesh, type MeshStandardMaterial } from 'three'

export interface SatelliteSpec {
  id: string
  label: string
  pulse: number
}

/**
 * Satélites de un agente: su modelo en Foundry y su herramienta. Orbitan el orbe y se encienden
 * (con un haz desde el agente) cada vez que se los llama.
 */
export function Satellites({ agent, specs, color }: { agent: string; specs: SatelliteSpec[]; color: Color }) {
  return (
    <>
      {specs.map((s, i) => (
        <Satellite key={s.id} spec={s} color={color} phase={(i / specs.length) * Math.PI * 2 + agent.length} />
      ))}
    </>
  )
}

function Satellite({ spec, color, phase }: { spec: SatelliteSpec; color: Color; phase: number }) {
  const pivot = useRef<Group>(null)
  const ball = useRef<Mesh>(null)
  const flash = useRef(0)
  const lastPulse = useRef(spec.pulse)
  const beam = useRef<any>(null)
  const label = useRef<HTMLDivElement>(null)

  useFrame((state, dt) => {
    if (spec.pulse !== lastPulse.current) {
      lastPulse.current = spec.pulse
      flash.current = 1
    }
    flash.current = MathUtils.damp(flash.current, 0, 1.6, dt)
    const t = state.clock.elapsedTime * 0.35 + phase
    const r = 1.65
    if (pivot.current) pivot.current.position.set(Math.cos(t) * r, Math.sin(t * 1.3) * 0.35 + 0.2, Math.sin(t) * r)
    const m = ball.current?.material as MeshStandardMaterial | undefined
    const used = spec.pulse > 0
    if (m) m.emissiveIntensity = (used ? 0.8 : 0.15) + flash.current * 5
    if (ball.current) ball.current.scale.setScalar(1 + flash.current * 0.8)
    if (beam.current?.material) beam.current.material.opacity = flash.current * 0.9
    // la etiqueta aparece solo mientras el satélite está siendo llamado
    if (label.current) label.current.style.opacity = String(Math.min(flash.current * 2.2, 1))
    if (beam.current && pivot.current) {
      const p = pivot.current.position
      beam.current.geometry.setPositions([0, 0, 0, p.x, p.y, p.z])
    }
  })

  return (
    <>
      <Line ref={beam} points={[[0, 0, 0], [1, 0, 0]]} color={color} lineWidth={2} transparent opacity={0} toneMapped={false} />
      <group ref={pivot}>
        <mesh ref={ball}>
          <octahedronGeometry args={[0.13, 0]} />
          <meshStandardMaterial color="#0b0e14" emissive={color} emissiveIntensity={0.15} toneMapped={false} />
        </mesh>
        <Html position={[0, -0.42, 0]} center zIndexRange={[5, 0]} style={{ pointerEvents: 'none' }}>
          <div ref={label} className="sat-label used" style={{ opacity: 0 }}>
            {spec.label}
          </div>
        </Html>
      </group>
    </>
  )
}
