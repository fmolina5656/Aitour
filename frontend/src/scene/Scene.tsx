import { Grid, PerformanceMonitor, Stars } from '@react-three/drei'
import { Canvas } from '@react-three/fiber'
import { Bloom, EffectComposer, Vignette } from '@react-three/postprocessing'
import { useMemo, useState } from 'react'
import { money } from '../agents'
import type { AgentId, StageState } from '../types'
import { AgentOrb } from './AgentOrb'
import { CameraRig } from './CameraRig'
import { Links } from './Comets'
import { Core } from './Core'
import { AGENT_POS, cssColor } from './layout'
import type { SatelliteSpec } from './Satellites'

// Calidad: ?quality=high|low en la URL la fuerza; si no, VITE_QUALITY=low o degradación automática por FPS.
const FORCED = new URLSearchParams(location.search).get('quality')
const LOW = FORCED ? FORCED === 'low' : import.meta.env.VITE_QUALITY === 'low'

const TOOLS: Partial<Record<AgentId, { id: string; label: string }>> = {
  arquitecto: { id: 'tool-catalogo', label: 'Catálogo Azure' },
  financiero: { id: 'tool-calc', label: 'Calculador' },
  riesgo: { id: 'tool-normas', label: 'Normas MX' },
}

const AGENTS: AgentId[] = ['arquitecto', 'financiero', 'riesgo', 'redactor']

export function Scene({ s }: { s: StageState }) {
  // Si la laptop del stand no sostiene los FPS, se apagan bloom y estrellas automáticamente.
  const [low, setLow] = useState(LOW)
  const focus = s.live ? AGENT_POS[s.live.agent] : null
  const sats = useMemo(() => {
    const out = {} as Record<AgentId, SatelliteSpec[]>
    for (const a of AGENTS) {
      out[a] = [{ id: `model-${a}`, label: s.models[a] ?? 'modelo', pulse: s.subPulses[`model-${a}`] ?? 0 }]
      const tool = TOOLS[a]
      if (tool) out[a].push({ id: tool.id, label: tool.label, pulse: s.subPulses[tool.id] ?? 0 })
    }
    return out
  }, [s.models, s.subPulses])

  const done = s.status.onepager === 'done'
  const theme = useMemo(() => ({ bg: cssColor('--bg'), cell: cssColor('--grid-cell'), section: cssColor('--grid-section') }), [])
  const blocked = !!s.blocked
  const coreTitle = blocked ? 'Solicitud bloqueada' : done ? 'One-pager listo' : s.brief ? 'Tu problema' : 'Esperando tu problema'
  const coreSub = blocked
    ? s.blocked?.kind === 'jailbreak' ? 'Prompt Shields' : 'Fuera de alcance'
    : done ? (s.cost ? `${money(s.cost.total_usd)}/mes estimado` : undefined) : s.brief?.industria

  return (
    <Canvas className="scene" dpr={[1, 1.5]} camera={{ position: [3.6, 10, 19], fov: 40 }} gl={{ antialias: true, powerPreference: 'high-performance' }}>
      {!FORCED && <PerformanceMonitor onDecline={() => setLow(true)} onFallback={() => setLow(true)} flipflops={3} />}
      <color attach="background" args={[theme.bg]} />
      <fog attach="fog" args={[theme.bg, 20, 42]} />
      <ambientLight intensity={0.25} />
      <directionalLight position={[4, 10, 6]} intensity={0.6} />
      {!low && <Stars radius={70} depth={40} count={2600} factor={3.2} saturation={0} fade speed={0.4} />}
      <Grid
        position={[0, -1.7, -2]}
        infiniteGrid
        cellSize={0.6}
        cellThickness={0.6}
        cellColor={theme.cell}
        sectionSize={3}
        sectionThickness={1}
        sectionColor={theme.section}
        fadeDistance={30}
        fadeStrength={1.6}
      />
      {AGENTS.map((a) => (
        <AgentOrb key={a} id={a} status={s.status[a] ?? 'idle'} chip={s.chips[a]} satellites={sats[a]} />
      ))}
      {/* el núcleo va después de los orbes: su Html necesita el contenedor ya montado */}
      <Core title={coreTitle} subtitle={coreSub} done={done} blocked={blocked} active={s.phase === 'swarm'} />
      <Links handoffs={s.handoffs} />
      <CameraRig focus={focus} />
      {!low && (
        <EffectComposer multisampling={0}>
          <Bloom mipmapBlur intensity={0.9} luminanceThreshold={0.35} luminanceSmoothing={0.2} radius={0.6} />
          <Vignette offset={0.25} darkness={0.7} />
        </EffectComposer>
      )}
    </Canvas>
  )
}
