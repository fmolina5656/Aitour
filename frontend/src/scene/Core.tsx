import { Billboard, Html } from '@react-three/drei'
import { useFrame } from '@react-three/fiber'
import { useMemo, useRef } from 'react'
import { AdditiveBlending, CanvasTexture, Color, MathUtils, SRGBColorSpace, TextureLoader, type Group, type Mesh, type MeshBasicMaterial } from 'three'
import { audioLevel } from '../voice/audio'
import { CORE, cssColor } from './layout'

const GLITCH_OPEN = '/brand/glitch-open.webp'
const GLITCH_BLINK = '/brand/glitch-blink.webp' // ojos cerrados: parpadeo y cara feliz al terminar
const SIZE = 2.6
// Un poco por debajo de blanco: con toneMapped=false conserva los colores de la imagen y el bloom no lo quema
const BASE = new Color(0.78, 0.78, 0.78)

/** Halo radial (canvas → textura) que late detrás de Glitch. */
function haloTexture() {
  const c = document.createElement('canvas')
  c.width = c.height = 256
  const g = c.getContext('2d')!
  const grad = g.createRadialGradient(128, 128, 0, 128, 128, 128)
  grad.addColorStop(0, 'rgba(255,255,255,0.9)')
  grad.addColorStop(0.45, 'rgba(255,255,255,0.35)')
  grad.addColorStop(1, 'rgba(255,255,255,0)')
  g.fillStyle = grad
  g.fillRect(0, 0, 256, 256)
  return new CanvasTexture(c)
}

/**
 * Núcleo: Glitch, la mascota de Readymind. Flota y parpadea; durante la entrevista rebota con la voz de la
 * recepcionista (y se inclina hacia el visitante cuando habla). Al terminar pone cara feliz y emite una onda
 * expansiva; si se bloquea la solicitud, se pone rojo y tiembla.
 */
export function Core({ title, subtitle, done, blocked, active, reactive = false, yielding = false }: { title: string; subtitle?: string; done: boolean; blocked: boolean; active: boolean; reactive?: boolean; yielding?: boolean }) {
  const accent = useMemo(() => cssColor('--core'), [])
  const finale = useMemo(() => cssColor('--core-done'), [])
  const alert = useMemo(() => cssColor('--alert'), [])
  const tex = useMemo(() => {
    const loader = new TextureLoader()
    const load = (url: string) => {
      const t = loader.load(url)
      t.colorSpace = SRGBColorSpace
      return t
    }
    return { open: load(GLITCH_OPEN), blink: load(GLITCH_BLINK), halo: haloTexture() }
  }, [])
  const body = useRef<Group>(null)
  const face = useRef<Mesh>(null)
  const halo = useRef<Mesh>(null)
  const wave = useRef<Mesh>(null)
  const waveT = useRef(done ? 1 : 0)
  const talk = useRef(0) // nivel suavizado de la voz de la recepcionista
  const listen = useRef(0) // nivel suavizado del micrófono
  const nextBlink = useRef(2)
  const blinkUntil = useRef(0)
  const presence = useRef(1) // 1 = protagonista; baja cuando un agente piensa y le cede la escena
  const tint = useMemo(() => new Color(), [])

  useFrame((state, dt) => {
    const t = state.clock.elapsedTime
    // audioLevel ya viene normalizado 0..1 (audio.ts); no volver a amplificar o satura y deja de "hablar"
    const agentLvl = reactive ? audioLevel.agent : 0
    const micLvl = reactive ? audioLevel.mic : 0
    // sube rápido y baja un poco más lento: se lee como sílabas, no como ruido
    talk.current = MathUtils.damp(talk.current, agentLvl, agentLvl > talk.current ? 30 : 12, dt)
    listen.current = MathUtils.damp(listen.current, micLvl, 6, dt)
    // mientras un agente piensa, Glitch se achica y se apaga (≈0.5 s); vuelve al terminar o al hablar
    presence.current = MathUtils.damp(presence.current, yielding && !done ? 0 : 1, 4, dt)
    const p = presence.current

    // parpadeo cada 2–5 s (y doble parpadeo de vez en cuando)
    if (t > nextBlink.current) {
      blinkUntil.current = t + 0.13
      nextBlink.current = t + (Math.random() < 0.2 ? 0.3 : 2 + Math.random() * 3)
    }
    const eyesClosed = done || t < blinkUntil.current
    const m = face.current?.material as MeshBasicMaterial | undefined
    if (m) {
      const map = eyesClosed ? tex.blink : tex.open
      if (m.map !== map) m.map = map
      tint.copy(blocked ? alert : BASE).multiplyScalar(0.55 + 0.45 * p)
      m.color.lerp(tint, 1 - Math.exp(-4 * dt))
    }

    if (body.current) {
      const tk = talk.current
      // flotar en reposo; rebote y squash & stretch al hablar; inclinarse hacia el visitante al escucharlo
      const bob = Math.sin(t * 1.4) * 0.12 + tk * 0.25
      const shake = blocked ? Math.sin(t * 38) * 0.06 : 0
      body.current.position.set(shake, bob, listen.current * 0.5)
      const base = (done ? 1.12 : 1) * (0.62 + 0.38 * p)
      body.current.scale.set(base * (1 - tk * 0.08), base * (1 + tk * 0.16), 1)
      const sway = active ? Math.sin(t * 1.1) * 0.06 : Math.sin(t * 0.7) * 0.03
      body.current.rotation.z = MathUtils.damp(body.current.rotation.z, sway + Math.sin(t * 9) * tk * 0.07, 8, dt)
    }

    const hm = halo.current?.material as MeshBasicMaterial | undefined
    if (hm) {
      hm.color.lerp(blocked ? alert : done ? finale : accent, 1 - Math.exp(-3 * dt))
      const target = blocked ? 0.5 + Math.sin(t * 6) * 0.3 : done ? 0.75 : 0.22 + Math.sin(t * 1.6) * 0.06 + talk.current * 0.6 + listen.current * 0.25
      hm.opacity = MathUtils.damp(hm.opacity, target * (0.35 + 0.65 * p), 10, dt)
      halo.current!.scale.setScalar((1 + talk.current * 0.25) * (0.62 + 0.38 * p))
    }

    // onda expansiva al convertirse en one-pager
    waveT.current = done ? Math.min(waveT.current + dt / 1.8, 1) : 0
    if (wave.current) {
      wave.current.scale.setScalar(1 + waveT.current * 9)
      ;(wave.current.material as MeshBasicMaterial).opacity = done ? (1 - waveT.current) * 0.6 : 0
    }
  })

  return (
    <group position={CORE}>
      <Billboard>
        {/* Glitch se dibuja al final y sin depth test: cables y cometas pasan POR DETRÁS de él, nunca encima */}
        <mesh ref={halo} position={[0, 0, -0.05]} renderOrder={10}>
          <planeGeometry args={[SIZE * 1.9, SIZE * 1.9]} />
          <meshBasicMaterial map={tex.halo} color={accent} transparent opacity={0.2} blending={AdditiveBlending} depthWrite={false} depthTest={false} toneMapped={false} />
        </mesh>
        <group ref={body}>
          <mesh ref={face} renderOrder={11}>
            <planeGeometry args={[SIZE, SIZE]} />
            <meshBasicMaterial map={tex.open} color={BASE} transparent alphaTest={0.05} depthWrite={false} depthTest={false} toneMapped={false} />
          </mesh>
        </group>
      </Billboard>
      <mesh ref={wave} rotation={[-Math.PI / 2, 0, 0]}>
        <ringGeometry args={[0.9, 1, 96]} />
        <meshBasicMaterial color={finale} transparent opacity={0} depthWrite={false} toneMapped={false} />
      </mesh>
      <Html position={[0, -2.25, 0]} center zIndexRange={[10, 0]} style={{ pointerEvents: 'none' }}>
        <div className={`core-label ${done ? 'done' : ''} ${blocked ? 'blocked' : ''}`}>
          <div className="core-title">{title}</div>
          {subtitle && <div className="core-sub">{subtitle}</div>}
        </div>
      </Html>
    </group>
  )
}
