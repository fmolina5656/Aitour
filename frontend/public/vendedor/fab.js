/* Botón flotante "Lead rápido" para el equipo del stand: un chat que pide los datos del visitante y los guarda
   como ficha del vendedor (POST /api/vendedor/visita, ver backend/app/seller.py). Solo guarda: no muestra leads.
   Aparece en las páginas cuyo <html> tiene data-fab="1" (la vista tablet de la demo lo activa sola y /casos lo trae fijo).
   El PIN del stand se pide una vez por dispositivo. */
(() => {
  if (window.__rmFab) return
  window.__rmFab = true
  const store = {
    get: (k) => { try { return localStorage.getItem(k) || '' } catch { return '' } },
    set: (k, v) => { try { v ? localStorage.setItem(k, v) : localStorage.removeItem(k) } catch {} },
  }
  const PIN_KEY = 'vend.fabpin', ME_KEY = 'vend.me'
  const EMAIL = /^[^\s@]+@[^\s@]+\.[^\s@]{2,}$/
  const IND = ['🏦 Finanzas', '🏭 Energía / Industria', '🛍 Retail', '🩺 Seguros / Salud', '🛡 Legal / Seguridad / TI', '✨ Otra']
  const INT = [['🗓 Taller', 'taller'], ['🚀 Piloto', 'piloto'], ['📄 Propuesta', 'propuesta'], ['ℹ️ Info', 'info'], ['👀 Curioso', 'curioso']]
  const esc = (s) => String(s ?? '').replace(/[&<>"]/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' })[c])

  const css = `
  .rmf-btn { position: fixed; right: 20px; bottom: var(--fab-bottom, 20px); z-index: 2147483000; width: 62px; height: 62px; border-radius: 50%; border: 0; cursor: pointer;
    background: linear-gradient(135deg, #66de7f, #397ef6); color: #04121b; font-size: 28px; box-shadow: 0 10px 30px rgba(0,0,0,.5); display: none; align-items: center; justify-content: center; }
  html[data-fab="1"] .rmf-btn { display: flex; }
  .rmf-btn:active { transform: scale(.95); }
  .rmf-panel { position: fixed; right: 20px; bottom: calc(var(--fab-bottom, 20px) + 76px); z-index: 2147483000; width: min(400px, calc(100vw - 24px)); height: min(600px, calc(100dvh - var(--fab-bottom, 20px) - 110px));
    display: none; flex-direction: column; background: #0a1526; color: #f3f6fa; border: 1px solid #2a4268; border-radius: 20px; box-shadow: 0 24px 70px rgba(0,0,0,.6);
    font-family: 'Satoshi', 'Segoe UI', system-ui, sans-serif; overflow: hidden; }
  .rmf-panel.on { display: flex; }
  .rmf-head { display: flex; align-items: center; gap: 10px; padding: 12px 14px; border-bottom: 1px solid #1f3150; background: #0c1a2e; }
  .rmf-head b { font-size: 16px; } .rmf-head small { display: block; color: #7d8ca2; font-size: 12px; }
  .rmf-head .rmf-x { margin-left: auto; background: none; border: 0; color: #7d8ca2; font-size: 24px; cursor: pointer; line-height: 1; }
  .rmf-log { flex: 1; overflow-y: auto; padding: 14px; display: flex; flex-direction: column; gap: 8px; }
  .rmf-m { max-width: 85%; padding: 9px 12px; border-radius: 14px; font-size: 15.5px; line-height: 1.4; }
  .rmf-m.bot { align-self: flex-start; background: #13233c; border-bottom-left-radius: 4px; }
  .rmf-m.me { align-self: flex-end; background: #66de7f; color: #04121b; font-weight: 600; border-bottom-right-radius: 4px; }
  .rmf-m.ok { background: #0f2a1a; border: 1px solid #66de7f; }
  .rmf-m.err { background: #2a1010; border: 1px solid #ff7a7a; color: #ffc2c2; }
  .rmf-sum { font-size: 14px; line-height: 1.55; } .rmf-sum span { color: #7d8ca2; }
  .rmf-chips { display: flex; flex-wrap: wrap; gap: 6px; padding: 0 14px 10px; }
  .rmf-chips button { font: inherit; font-size: 14.5px; color: #f3f6fa; background: #08111f; border: 1px solid #2a4268; border-radius: 99px; padding: 9px 13px; cursor: pointer; }
  .rmf-chips button.pri { background: #66de7f; color: #04121b; border-color: #66de7f; font-weight: 700; }
  .rmf-in { display: flex; gap: 8px; padding: 10px 12px 12px; border-top: 1px solid #1f3150; }
  .rmf-in input { flex: 1; min-width: 0; font: inherit; font-size: 16px; color: #f3f6fa; background: #08111f; border: 1px solid #2a4268; border-radius: 12px; padding: 11px 12px; }
  .rmf-in input:focus { outline: none; border-color: #66de7f; }
  .rmf-in button { font: inherit; font-weight: 700; font-size: 16px; color: #04121b; background: #66de7f; border: 0; border-radius: 12px; padding: 0 16px; cursor: pointer; }
  .rmf-in.off { display: none; }
  .rmf-foot { padding: 0 14px 10px; font-size: 12px; color: #7d8ca2; } .rmf-foot a { color: #7d8ca2; cursor: pointer; text-decoration: underline; }`

  function mount() {
    const st = document.createElement('style'); st.textContent = css; document.head.appendChild(st)
    const btn = document.createElement('button')
    btn.className = 'rmf-btn'; btn.title = 'Lead rápido (equipo del stand)'; btn.setAttribute('aria-label', 'Guardar un lead'); btn.textContent = '💼'
    const panel = document.createElement('div')
    panel.className = 'rmf-panel'; panel.setAttribute('role', 'dialog'); panel.setAttribute('aria-label', 'Lead rápido')
    panel.innerHTML = `<div class="rmf-head"><span style="font-size:22px">💼</span><div><b>Lead rápido</b><small id="rmf-who">Equipo Readymind</small></div><button class="rmf-x" aria-label="Cerrar">×</button></div>
      <div class="rmf-log"></div><div class="rmf-chips"></div>
      <form class="rmf-in"><input autocomplete="off" /><button type="submit">➤</button></form>
      <div class="rmf-foot"><a data-a="reset">Empezar de nuevo</a> · <a data-a="logout">Cerrar sesión en este equipo</a></div>`
    document.body.append(btn, panel)
    // las teclas del chat no deben disparar los atajos de la página (R reinicia la demo, ← → cambian de caso…)
    panel.addEventListener('keydown', (e) => { if (e.key === 'Escape') toggle(false); e.stopPropagation() })
    const $ = (s) => panel.querySelector(s)
    const log = $('.rmf-log'), chips = $('.rmf-chips'), form = $('.rmf-in'), input = $('.rmf-in input')
    let onAnswer = null, data = {}, started = false

    const say = (html, cls = 'bot') => { const d = document.createElement('div'); d.className = 'rmf-m ' + cls; d.innerHTML = html; log.appendChild(d); log.scrollTop = log.scrollHeight }
    // pregunta: texto libre (con validación) y/o opciones; skip = botón "Saltar"
    function ask(q, { type = 'text', placeholder = '', options = [], skip = false, validate } = {}) {
      return new Promise((resolve) => {
        if (q) say(esc(q))
        chips.innerHTML = options.map(([t, v], i) => `<button type="button" data-i="${i}" class="${v === '__primary' ? 'pri' : ''}">${esc(t)}</button>`).join('') +
          (skip ? '<button type="button" data-skip="1">Saltar</button>' : '')
        const free = type !== 'none'
        form.classList.toggle('off', !free)
        input.type = type === 'pin' ? 'password' : type === 'email' ? 'email' : 'text'
        input.inputMode = type === 'pin' ? 'numeric' : type === 'email' ? 'email' : 'text'
        input.placeholder = placeholder; input.value = ''
        if (free && matchMedia('(pointer: fine)').matches) input.focus()
        const done = (value, shown) => { chips.innerHTML = ''; onAnswer = null; if (shown !== null) say(esc(shown || 'Saltado'), 'me'); resolve(value) }
        chips.onclick = (e) => {
          const b = e.target.closest('button'); if (!b) return
          if (b.dataset.skip) return done('', '')
          const [t, v] = options[+b.dataset.i]; done(v, t)
        }
        onAnswer = (raw) => {
          const v = raw.trim(); if (!v) return
          const err = validate?.(v); if (err) return say(esc(err), 'err')
          done(v, type === 'pin' ? '••••' : v)
        }
      })
    }
    form.addEventListener('submit', (e) => { e.preventDefault(); onAnswer?.(input.value) })

    async function api(path, pin, body) {
      const r = await fetch('/api/vendedor' + path, { method: 'POST', headers: { 'Content-Type': 'application/json', 'X-Seller-Pin': pin }, body: body ? JSON.stringify(body) : undefined })
      const j = await r.json().catch(() => ({}))
      if (!r.ok) { const e = new Error(typeof j.detail === 'string' ? j.detail : 'No se pudo guardar'); e.status = r.status; throw e }
      return j
    }

    async function login() {
      let pin = store.get(PIN_KEY)
      while (true) {
        if (!pin) pin = await ask('Hola 👋 Esto es solo para el equipo de Readymind. ¿Cuál es el PIN del stand?', { type: 'pin', placeholder: 'PIN' })
        try { await api('/login', pin); store.set(PIN_KEY, pin); break }
        catch (e) {
          say(esc(e.status === 401 ? 'PIN incorrecto, prueba otra vez.' : e.message), 'err'); pin = ''
          if (e.status === 503 || e.status === 429) return false
        }
      }
      if (!store.get(ME_KEY)) store.set(ME_KEY, await ask('¿Quién atiende? (tu nombre, para saber de quién es cada lead)', { placeholder: 'Ej. Karem' }))
      $('#rmf-who').textContent = 'Atiende: ' + store.get(ME_KEY)
      return true
    }

    async function flow() {
      if (!(await login())) return
      while (true) {
        data = {}
        say('Nuevo lead ✍️')
        data.nombre = await ask('¿Cómo se llama?', { placeholder: 'Nombre y apellido', validate: (v) => v.length < 2 ? 'Escribe al menos 2 letras' : '' })
        data.empresa = await ask('¿De qué empresa es?', { placeholder: 'Empresa', skip: true })
        data.correo = await ask('¿Su correo?', { type: 'email', placeholder: 'nombre@empresa.com', skip: true, validate: (v) => EMAIL.test(v) ? '' : 'Ese correo no parece válido' })
        data.industria = await ask('¿De qué industria?', { type: 'none', options: IND.map((t) => [t, t.replace(/^\S+\s/, '')]), skip: true })
        data.interes = await ask('¿Qué le interesa?', { type: 'none', options: INT })
        data.nota = await ask('¿Alguna nota? (qué problema contó, próximo paso…)', { placeholder: 'Nota', skip: true })
        const row = (k, v) => v ? `<div><span>${k}:</span> ${esc(v)}</div>` : ''
        say(`<div class="rmf-sum"><b>¿Lo guardo así?</b>${row('Nombre', data.nombre)}${row('Empresa', data.empresa)}${row('Correo', data.correo)}${row('Industria', data.industria)}${row('Interés', INT.find((x) => x[1] === data.interes)?.[0])}${row('Nota', data.nota)}</div>`)
        const ok = await ask('', { type: 'none', options: [['✅ Guardar', '__primary'], ['✏️ Empezar de nuevo', 'redo']] })
        if (ok === 'redo') continue
        try {
          await api('/visita', store.get(PIN_KEY), { ...data, interes: data.interes || 'info', vendedor: store.get(ME_KEY) })
          say(`✅ Lead de <b>${esc(data.nombre)}</b> guardado. Lo ves en /vendedor y en el Excel del día.`, 'ok')
        } catch (e) {
          if (e.status === 401) { store.set(PIN_KEY, ''); say('El PIN cambió: ingrésalo de nuevo.', 'err'); if (!(await login())) return; continue }
          say(esc(e.message) + ' Revisa la conexión e intenta otra vez.', 'err')
        }
        await ask('', { type: 'none', options: [['➕ Otro lead', '__primary']] })
      }
    }

    function restart() { log.innerHTML = ''; chips.innerHTML = ''; onAnswer = null; started = true; flow() }
    function toggle(on) {
      panel.classList.toggle('on', on)
      btn.textContent = on ? '×' : '💼'
      if (on && !started) restart()
    }
    btn.onclick = () => toggle(!panel.classList.contains('on'))
    $('.rmf-x').onclick = () => toggle(false)
    $('.rmf-foot').onclick = (e) => {
      const a = e.target.closest('a'); if (!a) return
      if (a.dataset.a === 'logout') { store.set(PIN_KEY, ''); store.set(ME_KEY, ''); $('#rmf-who').textContent = 'Equipo Readymind' }
      restart()
    }
  }
  if (document.body) mount(); else document.addEventListener('DOMContentLoaded', mount)
})()
