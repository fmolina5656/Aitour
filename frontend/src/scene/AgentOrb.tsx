import { Html } from '@react-three/drei'
import { useFrame } from '@react-three/fiber'
import { useMemo, useRef } from 'react'
import { MathUtils, type Group, type Mesh, type MeshStandardMaterial } from 'three'
import { ACTOR_META } from '../agents'
import type { AgentId, NodeStatus } from '../types'
import { AGENT_POS, agentColor, cssColor } from './layout'
import { Satellites, type SatelliteSpec } from './Satellites'

const TARGET_GLOW: Record<NodeStatus, number> = { idle: 0.12, running: 1.8, done: 0.55, objected: 1.1 }

/** Orbe de luz de un agente: brilla mientras piensa, queda encendido al terminar, destella en ámbar si objeta. */
export function AgentOrb({ id, status, chip, satellites }: { id: AgentId; status: NodeStatus; chip?: string; satellites: SatelliteSpec[] }) {
  const color = useMemo(() => agentColor(id), [id])
  const alert = useMemo(() => cssColor('--alert'), [])
  const group = useRef<Group>(null)
  const core = useRef<Mesh>(null)
  const ring = useRef<Mesh>(null)
  const ring2 = useRef<Mesh>(null)
  const glow = useRef(TARGET_GLOW.idle)
  const flash = useRef(0)
  const prevStatus = useRef(status)
  if (prevStatus.current !== status) {
    if (status === 'objected') flash.current = 1
    prevStatus.current = status
  }

  useFrame((state, dt) => {
    const t = state.clock.elapsedTime
    const running = status === 'running'
    glow.current = MathUtils.damp(glow.current, TARGET_GLOW[status] + (running ? Math.sin(t * 5) * 0.45 : 0), 4, dt)
    const mat = core.current?.material as MeshStandardMaterial | undefined
    if (mat) {
      mat.emissiveIntensity = glow.current
      // al objetar: destello ámbar breve y vuelve a su color (el orbe nunca pierde su identidad)
      flash.current = MathUtils.damp(flash.current, 0, 1.2, dt)
      mat.emissive.copy(color).lerp(alert, flash.current)
    }
    if (group.current) {
      group.current.position.y = Math.sin(t * 0.8 + AGENT_POS[id].x) * 0.12
      const s = MathUtils.damp(group.current.scale.x, running ? 1.15 : 1, 5, dt)
      group.current.scale.setScalar(s)
    }
    for (const [r, speed] of [[ring, 1.4], [ring2, -0.9]] as const) {
      if (!r.current) continue
      r.current.rotation.z += dt * speed * (running ? 2.2 : 0.4)
      const m = r.current.material as MeshStandardMaterial
      m.emissive.copy(status === 'objected' ? alert : color)
      m.opacity = MathUtils.damp(m.opacity, running ? 0.95 : status === 'idle' ? 0.08 : 0.35, 4, dt)
    }
  })

  const meta = ACTOR_META[id]
  return (
    <group position={AGENT_POS[id]}>
      <group ref={group}>
        <mesh ref={core}>
          <icosahedronGeometry args={[0.62, 6]} />
          <meshStandardMaterial color="#0b0e14" emissive={color} emissiveIntensity={0.2} roughness={0.35} metalness={0.2} toneMapped={false} />
        </mesh>
        {/* halo */}
        <mesh scale={1.3}>
          <sphereGeometry args={[0.62, 32, 32]} />
          <meshBasicMaterial color={color} transparent opacity={0.04} depthWrite={false} />
        </mesh>
        <mesh ref={ring} rotation={[Math.PI / 2.3, 0, 0]}>
          <torusGeometry args={[1.05, 0.02, 8, 96, Math.PI * 1.4]} />
          <meshStandardMaterial color={color} emissive={color} emissiveIntensity={2.5} transparent opacity={0.1} toneMapped={false} />
        </mesh>
        <mesh ref={ring2} rotation={[Math.PI / 1.7, 0.4, 0]}>
          <torusGeometry args={[1.28, 0.012, 8, 96, Math.PI * 0.9]} />
          <meshStandardMaterial color={color} emissive={color} emissiveIntensity={2} transparent opacity={0.1} toneMapped={false} />
        </mesh>
      </group>
      <Satellites agent={id} specs={satellites} color={color} />
      <Html position={AGENT_POS[id].z < -2 ? [0, 1.5, 0] : [0, -1.35, 0]} center zIndexRange={[10, 0]} style={{ pointerEvents: 'none' }}>
        <div className={`orb-label st-${status}`} style={{ ['--c' as string]: `#${color.getHexString()}` }}>
          <div className="orb-name">
            {meta.label}
            {status === 'done' && <span className="orb-badge ok">✓</span>}
            {status === 'objected' && <span className="orb-badge warn">!</span>}
          </div>
          <div className={`orb-chip ${chip ? 'has' : ''}`}>{chip ?? meta.role}</div>
        </div>
      </Html>
    </group>
  )
}
