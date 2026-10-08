import { useCallback, useEffect, useRef, useState } from 'react'
import { StandAudio } from './audio'

export type VoiceStatus = 'off' | 'connecting' | 'live' | 'text-only'

/**
 * Sesión de voz con la recepcionista. Si el micrófono no está disponible (permiso, ruido, hardware),
 * la entrevista sigue por teclado sobre el mismo canal: nunca se pierde la demo.
 */
export function useVoice() {
  const [status, setStatus] = useState<VoiceStatus>('off')
  const ws = useRef<WebSocket | null>(null)
  const audio = useRef<StandAudio | null>(null)

  const stop = useCallback(async () => {
    ws.current?.readyState === WebSocket.OPEN && ws.current.send(JSON.stringify({ type: 'stop' }))
    ws.current?.close()
    ws.current = null
    await audio.current?.stop()
    audio.current = null
    setStatus('off')
  }, [])

  const start = useCallback(async () => {
    await stop()
    setStatus('connecting')
    const proto = location.protocol === 'https:' ? 'wss' : 'ws'
    const sock = new WebSocket(`${proto}://${location.host}/ws/voice`)
    sock.binaryType = 'arraybuffer'
    ws.current = sock
    sock.onmessage = (m) => {
      if (m.data instanceof ArrayBuffer) audio.current?.play(m.data)
      else {
        const msg = JSON.parse(m.data)
        if (msg.type === 'interrupt') audio.current?.interrupt()
        if (msg.type === 'closed') void stop()
      }
    }
    sock.onclose = () => {
      void audio.current?.stop()
      setStatus('off')
    }
    await new Promise<void>((resolve, reject) => {
      sock.onopen = () => resolve()
      sock.onerror = () => reject(new Error('voz no disponible'))
    })
    try {
      const a = new StandAudio()
      await a.start((pcm) => sock.readyState === WebSocket.OPEN && sock.send(pcm))
      audio.current = a
      setStatus('live')
    } catch {
      setStatus('text-only') // sin micrófono: la recepcionista sigue por teclado
    }
  }, [stop])

  const sendText = useCallback((text: string) => {
    ws.current?.readyState === WebSocket.OPEN && ws.current.send(JSON.stringify({ type: 'text', text }))
  }, [])

  const confirm = useCallback(() => {
    ws.current?.readyState === WebSocket.OPEN && ws.current.send(JSON.stringify({ type: 'confirm' }))
  }, [])

  useEffect(() => () => void stop(), [stop])

  return { status, start, stop, sendText, confirm, active: status !== 'off' }
}
