import { Billboard, Html } from '@react-three/drei'
import { useFrame } from '@react-three/fiber'
import { useMemo, useRef } from 'react'
import { Color, MathUtils, type Group, type Mesh, type MeshBasicMaterial, type MeshStandardMaterial } from 'three'
import { ACTOR_META } from '../agents'
import type { AgentId, NodeStatus } from '../types'
import { GLITCH_BLINK, GLITCH_OPEN, tintedGlitch } from './glitchTextures'
import { agentColor, agentPos, cssColor } from './layout'
import { Satellites, type SatelliteSpec } from './Satellites'

const SIZE = 1.55
// Brillo del mini-Glitch por estado: apagado en espera, encendido mientras piensa
const TARGET_BRIGHT: Record<NodeStatus, number> = { idle: 0.42, running: 0.95, done: 0.8, objected: 0.9 }
const HAPPY_S = 1.6 // cara feliz al terminar
// Protagonismo: el agente que piensa crece y los demás se achican y se apagan un poco
export type Spotlight = 'me' | 'other' | 'none'
const SPOT_SCALE: Record<Spotlight, number> = { me: 1.5, other: 0.72, none: 1 }
const SPOT_DIM: Record<Spotlight, number> = { me: 1, other: 0.6, none: 1 }

/**
 * Mini-Glitch de un agente, con el color del agente: tenue en espera; mientras piensa se enciende, se mece,
 * parpadea más y le salen puntitos de "pensando…"; al terminar pone cara feliz; si objeta, destello ámbar.
 */
export function AgentOrb({ id, status, chip, satellites, spotlight = 'none', tablet = false }: { id: AgentId; status: NodeStatus; chip?: string; satellites: SatelliteSpec[]; spotlight?: Spotlight; tablet?: boolean }) {
  const pos = agentPos(id, tablet)
  const color = useMemo(() => agentColor(id), [id])
  const alert = useMemo(() => cssColor('--alert'), [])
  const tex = useMemo(() => ({ open: tintedGlitch(GLITCH_OPEN, color), blink: tintedGlitch(GLITCH_BLINK, color) }), [color])
  const tint = useMemo(() => new Color(), [])
  const group = useRef<Group>(null)
  const body = useRef<Group>(null)
  const face = useRef<Mesh>(null)
  const ring = useRef<Mesh>(null)
  const ring2 = useRef<Mesh>(null)
  const dots = useRef<Group>(null)
  const bright = useRef(TARGET_BRIGHT.idle)
  const flash = useRef(0)
  const happyUntil = useRef(0)
  const nextBlink = useRef(1 + Math.random() * 3)
  const blinkUntil = useRef(0)
  const prevStatus = useRef(status)
  const pendingStatus = useRef<NodeStatus | null>(null)
  if (prevStatus.current !== status) {
    pendingStatus.current = status
    prevStatus.current = status
  }

  useFrame((state, dt) => {
    const t = state.clock.elapsedTime
    const running = status === 'running'
    if (pendingStatus.current) {
      if (pendingStatus.current === 'objected') flash.current = 1
      if (pendingStatus.current === 'done') happyUntil.current = t + HAPPY_S
      pendingStatus.current = null
    }
    flash.current = MathUtils.damp(flash.current, 0, 1.2, dt)

    // parpadeo: más seguido mientras piensa
    if (t > nextBlink.current) {
      blinkUntil.current = t + 0.12
      nextBlink.current = t + (running ? 0.8 + Math.random() * 1.2 : 2.5 + Math.random() * 3.5)
    }
    const m = face.current?.material as MeshBasicMaterial | undefined
    if (m) {
      const map = t < blinkUntil.current || t < happyUntil.current ? tex.blink : tex.open
      if (m.map !== map) m.map = map
      bright.current = MathUtils.damp(bright.current, TARGET_BRIGHT[status] * SPOT_DIM[spotlight] + (running ? Math.sin(t * 5) * 0.08 : 0), 4, dt)
      tint.setScalar(bright.current).lerp(alert, flash.current * 0.7)
      m.color.copy(tint)
    }

    if (group.current) {
      group.current.position.y = Math.sin(t * 0.8 + pos.x) * 0.12
      // transición suave (≈0.5 s) para que el cambio de protagonista se lea como un movimiento, no un salto
      const s = MathUtils.damp(group.current.scale.x, SPOT_SCALE[spotlight], 4, dt)
      group.current.scale.setScalar(s)
    }
    if (body.current) {
      // pensando: se mece de lado a lado y sube y baja un poco, como cavilando; al objetar, un sacudón
      const ponder = running ? Math.sin(t * 2.2) * 0.14 : Math.sin(t * 0.6 + id.length) * 0.04
      body.current.rotation.z = MathUtils.damp(body.current.rotation.z, ponder + Math.sin(t * 40) * flash.current * 0.12, 6, dt)
      body.current.position.y = running ? Math.abs(Math.sin(t * 4.4)) * 0.08 : 0
    }

    // "pensando…": tres puntitos que saltan en secuencia sobre la cabeza
    if (dots.current) {
      dots.current.visible = running
      dots.current.children.forEach((d, i) => {
        d.position.y = SIZE * 0.62 + Math.max(0, Math.sin(t * 6 - i * 0.9)) * 0.16
      })
    }

    for (const [r, speed] of [[ring, 1.4], [ring2, -0.9]] as const) {
      if (!r.current) continue
      r.current.rotation.z += dt * speed * (running ? 2.2 : 0.4)
      const rm = r.current.material as MeshStandardMaterial
      rm.emissive.copy(status === 'objected' ? alert : color)
      rm.opacity = MathUtils.damp(rm.opacity, running ? 0.95 : status === 'idle' ? 0.08 : 0.35, 4, dt)
    }
  })

  const meta = ACTOR_META[id]
  return (
    <group position={pos}>
      <group ref={group}>
        <Billboard>
          <group ref={body}>
            {/* como el Glitch central: se dibuja después de cables y cometas, que pasan por detrás */}
            <mesh ref={face} renderOrder={9}>
              <planeGeometry args={[SIZE, SIZE]} />
              <meshBasicMaterial map={tex.open} transparent alphaTest={0.05} depthWrite={false} depthTest={false} toneMapped={false} />
            </mesh>
          </group>
          <group ref={dots} visible={false}>
            {[-0.26, 0, 0.26].map((x) => (
              <mesh key={x} position={[x, SIZE * 0.62, 0.05]} renderOrder={9}>
                <circleGeometry args={[0.085, 20]} />
                <meshBasicMaterial color={color} transparent depthTest={false} toneMapped={false} />
              </mesh>
            ))}
          </group>
        </Billboard>
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
      {/* etiqueta con margen para cuando el mini-Glitch crece por el protagonismo (×1.5) */}
      <Html position={pos.z < -2 ? [0, 1.6, 0] : [0, -1.75, 0]} center zIndexRange={[10, 0]} style={{ pointerEvents: 'none' }}>
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
