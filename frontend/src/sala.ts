/**
 * Sala del stand (la PC y cada tablet): cada una corre su propia sesión en el backend.
 * Se elige con ?sala=tablet1 en la URL y queda recordada en el dispositivo; sin sala, el backend usa la primera (pc).
 */
const KEY = 'aitour.sala'

function readSala(): string {
  const fromUrl = new URLSearchParams(location.search).get('sala')?.trim().toLowerCase() ?? ''
  try {
    if (fromUrl) localStorage.setItem(KEY, fromUrl)
    return fromUrl || localStorage.getItem(KEY) || ''
  } catch {
    return fromUrl // sin almacenamiento: la sala vale solo para esta carga
  }
}

export const SALA = readSala()

/** Agrega ?sala=… a una ruta del backend. */
export const withSala = (path: string) => (SALA ? `${path}${path.includes('?') ? '&' : '?'}sala=${encodeURIComponent(SALA)}` : path)

/** La sala guardada ya no existe en el backend: se olvida para que la próxima carga use la de por defecto. */
export function forgetSala() {
  try {
    localStorage.removeItem(KEY)
  } catch {
    // nada que olvidar
  }
}
