import { useFrame, useThree } from '@react-three/fiber'
import { useRef } from 'react'
import { MathUtils, Vector3 } from 'three'
import { CORE } from './layout'

// Encuadre base: la escena queda a la izquierda, dejando lugar a la conversación del panel derecho.
const BASE_POS = new Vector3(3.6, 10, 19)
const BASE_LOOK = new Vector3(4.1, -2.4, -2.2)

/** Cámara cinematográfica: se acerca suave al agente que habla y vuelve; balanceo lento en reposo. */
export function CameraRig({ focus }: { focus: Vector3 | null }) {
  const { camera } = useThree()
  const look = useRef(BASE_LOOK.clone())
  const desiredPos = new Vector3()
  const desiredLook = new Vector3()

  useFrame((state, dt) => {
    const t = state.clock.elapsedTime
    const f = focus ?? CORE
    const strength = focus ? 0.22 : 0
    desiredPos.copy(BASE_POS).addScaledVector(f.clone().sub(CORE), strength)
    desiredPos.z -= focus ? 1.5 : 0
    desiredPos.x += Math.sin(t * 0.11) * 0.7
    desiredPos.y += Math.sin(t * 0.07) * 0.25
    desiredLook.copy(BASE_LOOK).lerp(f.clone().setX(f.x + 4.1).setY(-2.4), focus ? 0.25 : 0)
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
