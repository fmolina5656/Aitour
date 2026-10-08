import { CanvasTexture, Color, SRGBColorSpace, type Texture } from 'three'

export const GLITCH_OPEN = '/brand/glitch-open.webp'
export const GLITCH_BLINK = '/brand/glitch-blink.webp' // ojos cerrados: parpadeo y cara feliz

const images = new Map<string, Promise<HTMLImageElement>>()
const cache = new Map<string, Texture>()

function loadImage(url: string) {
  let p = images.get(url)
  if (!p) {
    p = new Promise((resolve, reject) => {
      const img = new Image()
      img.onload = () => resolve(img)
      img.onerror = reject
      img.src = url
    })
    images.set(url, p)
  }
  return p
}

/**
 * Glitch recoloreado al tono de un agente. Cambia el TONO de cada píxel (conserva saturación y luminosidad):
 * el verde pasa al color del agente y el negro de los ojos y el chip queda negro. Multiplicar por el color
 * en el material daría un tono sucio.
 */
export function tintedGlitch(url: string, color: Color): Texture {
  const key = `${url}|${color.getHexString()}`
  const hit = cache.get(key)
  if (hit) return hit
  const canvas = document.createElement('canvas')
  canvas.width = canvas.height = 480 // tamaño de las imágenes de Glitch: transparente hasta que carga
  const tex = new CanvasTexture(canvas)
  tex.colorSpace = SRGBColorSpace
  cache.set(key, tex)

  const target = { h: 0, s: 0, l: 0 }
  color.getHSL(target)
  void loadImage(url).then((img) => {
    if (canvas.width !== img.naturalWidth || canvas.height !== img.naturalHeight) {
      // three reserva el tamaño en la GPU en el primer uso (storage inmutable): si cambia, hay que liberarla
      canvas.width = img.naturalWidth
      canvas.height = img.naturalHeight
      tex.dispose()
    }
    const g = canvas.getContext('2d', { willReadFrequently: true })!
    g.drawImage(img, 0, 0)
    const data = g.getImageData(0, 0, canvas.width, canvas.height)
    const px = data.data
    const c = new Color()
    const hsl = { h: 0, s: 0, l: 0 }
    for (let i = 0; i < px.length; i += 4) {
      if (px[i + 3] === 0) continue
      c.setRGB(px[i] / 255, px[i + 1] / 255, px[i + 2] / 255, SRGBColorSpace)
      c.getHSL(hsl, SRGBColorSpace)
      // algo de la saturación y la luminosidad del color destino, para que cada agente se distinga (el
      // violeta lavanda del Redactor no quede igual al azul del Arquitecto); ojos y chip (oscuros) no se tocan
      const l = hsl.l < 0.25 ? hsl.l : hsl.l * 0.65 + target.l * 0.35
      c.setHSL(target.h, Math.min(1, hsl.s * 0.6 + target.s * 0.4), l, SRGBColorSpace)
      const rgb = { r: 0, g: 0, b: 0 }
      c.getRGB(rgb, SRGBColorSpace)
      px[i] = rgb.r * 255
      px[i + 1] = rgb.g * 255
      px[i + 2] = rgb.b * 255
    }
    g.putImageData(data, 0, 0)
    tex.needsUpdate = true
  })
  return tex
}
