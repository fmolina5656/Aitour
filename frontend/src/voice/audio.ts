/**
 * Audio del stand: micrófono → PCM16 mono 24 kHz (lo que espera el voice agent) y reproducción de la
 * recepcionista con corte inmediato cuando el visitante habla encima (barge-in).
 * Un solo AudioContext a 24 kHz: Chrome remuestrea el micrófono, sin código de resampling propio.
 */

const WORKLET = `
class Capture extends AudioWorkletProcessor {
  constructor() { super(); this.buf = new Int16Array(960); this.n = 0; this.sum = 0; }
  process(inputs) {
    const ch = inputs[0] && inputs[0][0];
    if (!ch) return true;
    for (let i = 0; i < ch.length; i++) {
      const s = Math.max(-1, Math.min(1, ch[i]));
      this.buf[this.n++] = s < 0 ? s * 0x8000 : s * 0x7fff;
      this.sum += s * s;
      if (this.n === this.buf.length) {            // 40 ms a 24 kHz
        this.port.postMessage({ pcm: this.buf.buffer, level: Math.sqrt(this.sum / this.n) }, [this.buf.buffer]);
        this.buf = new Int16Array(960); this.n = 0; this.sum = 0;
      }
    }
    return true;
  }
}
// Colchón anti-trabas: el audio llega por red a ritmo irregular (se midieron huecos de ~0.5 s dentro de una
// frase). No arranca hasta tener PREBUFFER de audio, o hasta que deje de llegar (frase corta). Si se vacía a
// mitad de frase, hace una pausa limpia y vuelve a juntar colchón en vez de entrecortarse.
const PREBUFFER = 0.3 * sampleRate;
const FLUSH_AFTER = 0.25; // s sin chunks nuevos: es el final de la frase, se reproduce lo que haya
class Player extends AudioWorkletProcessor {
  constructor() {
    super(); this.q = []; this.cur = null; this.pos = 0; this.queued = 0; this.playing = false; this.lastChunk = 0;
    this.port.onmessage = (e) => {
      if (e.data === 'clear') { this.q = []; this.cur = null; this.queued = 0; this.playing = false; return; }
      const c = new Int16Array(e.data); this.q.push(c); this.queued += c.length; this.lastChunk = currentTime;
    };
  }
  process(_, outputs) {
    const out = outputs[0][0];
    if (!this.playing && this.queued > 0 && (this.queued >= PREBUFFER || currentTime - this.lastChunk > FLUSH_AFTER)) this.playing = true;
    let level = 0;
    for (let i = 0; i < out.length; i++) {
      if (this.playing && (!this.cur || this.pos >= this.cur.length)) {
        this.cur = this.q.shift() || null; this.pos = 0;
        if (!this.cur) this.playing = false; // se vació: a juntar colchón otra vez
      }
      let v = 0;
      if (this.playing && this.cur) { v = this.cur[this.pos++] / 0x8000; this.queued--; }
      out[i] = v; level += v * v;
    }
    this.port.postMessage(Math.sqrt(level / out.length));
    return true;
  }
}
registerProcessor('rm-capture', Capture);
registerProcessor('rm-player', Player);
`

/** Nivel de audio compartido (0..1) para animar la escena 3D sin re-renderizar React. */
export const audioLevel = { mic: 0, agent: 0 }

export class StandAudio {
  private ctx: AudioContext | null = null
  private stream: MediaStream | null = null
  private player: AudioWorkletNode | null = null

  async start(onPcm: (pcm: ArrayBuffer) => void): Promise<void> {
    this.ctx = new AudioContext({ sampleRate: 24000, latencyHint: 'interactive' })
    const url = URL.createObjectURL(new Blob([WORKLET], { type: 'application/javascript' }))
    await this.ctx.audioWorklet.addModule(url)
    URL.revokeObjectURL(url)
    this.stream = await navigator.mediaDevices.getUserMedia({
      audio: { channelCount: 1, echoCancellation: true, noiseSuppression: true, autoGainControl: true },
    })
    const mic = this.ctx.createMediaStreamSource(this.stream)
    const capture = new AudioWorkletNode(this.ctx, 'rm-capture')
    capture.port.onmessage = (e) => {
      audioLevel.mic = Math.min(1, e.data.level * 4)
      onPcm(e.data.pcm)
    }
    mic.connect(capture)
    this.player = new AudioWorkletNode(this.ctx, 'rm-player')
    this.player.port.onmessage = (e) => (audioLevel.agent = Math.min(1, (e.data as number) * 4))
    this.player.connect(this.ctx.destination)
  }

  play(pcm: ArrayBuffer) {
    this.player?.port.postMessage(pcm, [pcm])
  }

  /** Barge-in: el visitante habló encima, se corta lo que estaba diciendo la recepcionista. */
  interrupt() {
    this.player?.port.postMessage('clear')
  }

  async stop() {
    this.stream?.getTracks().forEach((t) => t.stop())
    await this.ctx?.close().catch(() => undefined)
    this.ctx = null
    this.stream = null
    this.player = null
    audioLevel.mic = 0
    audioLevel.agent = 0
  }
}
