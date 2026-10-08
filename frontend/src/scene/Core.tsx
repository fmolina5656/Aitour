import { Html } from '@react-three/drei'
import { useFrame } from '@react-three/fiber'
import { useMemo, useRef } from 'react'
import { MathUtils, type Group, type Mesh, type MeshBasicMaterial, type MeshStandardMaterial } from 'three'
import { CORE, cssColor } from './layout'

/**
 * Núcleo: el problema del visitante. Al terminar, se transforma en el one-pager (crece, cambia de color
 * y emite una onda expansiva).
 */
export function Core({ title, subtitle, done, blocked, active }: { title: string; subtitle?: string; done: boolean; blocked: boolean; active: boolean }) {
  const accent = useMemo(() => cssColor('--core'), [])
  const finale = useMemo(() => cssColor('--core-done'), [])
  const alert = useMemo(() => cssColor('--alert'), [])
  const shell = useRef<Mesh>(null)
  const inner = useRef<Mesh>(null)
  const group = useRef<Group>(null)
  const wave = useRef<Mesh>(null)
  const waveT = useRef(done ? 1 : 0)

  useFrame((state, dt) => {
    const t = state.clock.elapsedTime
    if (shell.current) {
      shell.current.rotation.y += dt * (active ? 0.5 : 0.15)
      shell.current.rotation.x += dt * 0.07
    }
    const m = inner.current?.material as MeshStandardMaterial | undefined
    if (m) {
      m.emissive.lerp(blocked ? alert : done ? finale : accent, 1 - Math.exp(-3 * dt))
      // bloqueado: late como alarma; terminado: brillo pleno
      const target = blocked ? 1.2 + Math.sin(t * 6) * 0.6 : done ? 1.6 : 0.7 + Math.sin(t * 1.6) * 0.2
      m.emissiveIntensity = MathUtils.damp(m.emissiveIntensity, target, 3, dt)
    }
    if (group.current) group.current.scale.setScalar(MathUtils.damp(group.current.scale.x, done ? 1.12 : 1, 2.5, dt))
    // onda expansiva al convertirse en one-pager
    waveT.current = done ? Math.min(waveT.current + dt / 1.8, 1) : 0
    if (wave.current) {
      wave.current.scale.setScalar(1 + waveT.current * 9)
      ;(wave.current.material as MeshBasicMaterial).opacity = done ? (1 - waveT.current) * 0.6 : 0
    }
  })

  return (
    <group position={CORE}>
      <group ref={group}>
        <mesh ref={inner}>
          <sphereGeometry args={[0.5, 48, 48]} />
          <meshStandardMaterial color="#05070b" emissive={accent} emissiveIntensity={1} toneMapped={false} />
        </mesh>
        <mesh ref={shell}>
          <icosahedronGeometry args={[1.0, 1]} />
          <meshBasicMaterial color={blocked ? alert : done ? finale : accent} wireframe transparent opacity={0.35} />
        </mesh>
      </group>
      <mesh ref={wave} rotation={[-Math.PI / 2, 0, 0]}>
        <ringGeometry args={[0.9, 1, 96]} />
        <meshBasicMaterial color={finale} transparent opacity={0} depthWrite={false} toneMapped={false} />
      </mesh>
      <Html position={[0, -1.95, 0]} center zIndexRange={[10, 0]} style={{ pointerEvents: 'none' }}>
        <div className={`core-label ${done ? 'done' : ''} ${blocked ? 'blocked' : ''}`}>
          <div className="core-title">{title}</div>
          {subtitle && <div className="core-sub">{subtitle}</div>}
        </div>
      </Html>
    </group>
  )
}
