// Copia MediaPipe Tasks Vision (JS + WASM) a public/vision/lib para servirlo desde la propia app:
// en el stand la detección de personas no depende de ningún CDN. Corre solo antes de `npm run build` y `npm run dev`.
import { cpSync, mkdirSync } from 'node:fs'
import { dirname, join } from 'node:path'
import { fileURLToPath } from 'node:url'

const root = join(dirname(fileURLToPath(import.meta.url)), '..')
const src = join(root, 'node_modules', '@mediapipe', 'tasks-vision')
const dst = join(root, 'public', 'vision', 'lib')
mkdirSync(join(dst, 'wasm'), { recursive: true })
cpSync(join(src, 'vision_bundle.mjs'), join(dst, 'vision_bundle.mjs'))
for (const f of ['vision_wasm_internal.js', 'vision_wasm_internal.wasm', 'vision_wasm_nosimd_internal.js', 'vision_wasm_nosimd_internal.wasm']) {
  cpSync(join(src, 'wasm', f), join(dst, 'wasm', f))
}
console.log('MediaPipe copiado a public/vision/lib')
