import { useFrame, useThree } from '@react-three/fiber'
import { useRef } from 'react'
import { MathUtils, Vector3 } from 'three'
import { CORE } from './layout'

// Encuadre base: la escena queda a la izquierda, dejando lugar a la conversación del panel derecho.
const FRAMES = {
  stage: { pos: new Vector3(3.6, 10, 19), look: new Vector3(4.1, -2.4, -2.2) },
  // modo tablet: sin paneles, el universo va centrado y un poco más lejos para entrar en pantallas 4:3
  tablet: { pos: new Vector3(0, 11, 24), look: new Vector3(0, -1.2, -3) },
}

/** Cámara cinematográfica: se acerca suave al agente que habla y vuelve; balanceo lento en reposo. */
export function CameraRig({ focus, tablet = false }: { focus: Vector3 | null; tablet?: boolean }) {
  const { camera } = useThree()
  const frame = tablet ? FRAMES.tablet : FRAMES.stage
  const look = useRef(frame.look.clone())
  const desiredPos = new Vector3()
  const desiredLook = new Vector3()

  useFrame((state, dt) => {
    const t = state.clock.elapsedTime
    const f = focus ?? CORE
    const strength = focus ? 0.22 : 0
    desiredPos.copy(frame.pos).addScaledVector(f.clone().sub(CORE), strength)
    desiredPos.z -= focus ? 1.5 : 0
    desiredPos.x += Math.sin(t * 0.11) * 0.7
    desiredPos.y += Math.sin(t * 0.07) * 0.25
    desiredLook.copy(frame.look).lerp(f.clone().setX(f.x + frame.look.x).setY(frame.look.y), focus ? 0.25 : 0)
    camera.position.set(
      MathUtils.damp(camera.position.x, desiredPos.x, 1.6, dt),
      MathUtils.damp(camera.position.y, desiredPos.y, 1.6, dt),
      MathUtils.damp(camera.position.z, desiredPos.z, 1.6, dt),
    )
    look.current.set(
      MathUtils.damp(look.current.x, desiredLook.x, 1.8, dt),
      MathUtils.damp(look.current.y, desiredLook.y, 1.8, dt),
      MathUtils.damp(look.current.z, desiredLook.z, 1.8, dt),
    )
    camera.lookAt(look.current)
  })
  return null
}
