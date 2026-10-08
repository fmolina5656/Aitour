import { useState } from 'react'
import { api } from '../useStage'

const EXAMPLES = [
  { problema: 'Conciliamos a mano 5,000 facturas de proveedores al mes y nos atrasamos en los pagos', industria: 'Manufactura', volumen: '5,000 facturas/mes', datos: 'CFDI XML y PDF en SharePoint, ERP SAP' },
  { problema: 'Nuestro call center no da abasto con las preguntas repetitivas de clientes', industria: 'Retail', volumen: '20,000 llamadas/mes', datos: 'Grabaciones, FAQs y catálogo de productos' },
  { problema: 'Revisar expedientes de crédito nos toma 3 días por solicitud', industria: 'Servicios financieros', volumen: '1,200 solicitudes/mes', datos: 'Expedientes PDF, buró de crédito, CRM' },
]

/** Fallback a teclado (ruido de feria) y forma de desarrollar la Fase 1 sin voz. */
export function TextInput({ onClose }: { onClose: () => void }) {
  const [form, setForm] = useState(EXAMPLES[0])
  const [sending, setSending] = useState(false)
  const set = (k: keyof typeof form) => (e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement>) => setForm({ ...form, [k]: e.target.value })

  const submit = async (e: React.FormEvent) => {
    e.preventDefault()
    setSending(true)
    await api.startText(form)
    setSending(false)
    onClose()
  }

  return (
    <div className="overlay" onClick={onClose}>
      <form className="modal" onClick={(e) => e.stopPropagation()} onSubmit={submit}>
        <div className="modal-title">Cuéntanos tu problema</div>
        <div className="examples">
          {EXAMPLES.map((ex) => (
            <button type="button" key={ex.industria} className="chip" onClick={() => setForm(ex)}>
              {ex.industria}
            </button>
          ))}
        </div>
        <label>
          Problema
          <textarea autoFocus rows={3} value={form.problema} onChange={set('problema')} />
        </label>
        <div className="row3">
          <label>
            Industria
            <input value={form.industria} onChange={set('industria')} />
          </label>
          <label>
            Volumen
            <input value={form.volumen} onChange={set('volumen')} />
          </label>
          <label>
            Datos disponibles
            <input value={form.datos} onChange={set('datos')} />
          </label>
        </div>
        <div className="modal-actions">
          <button type="button" className="btn ghost" onClick={onClose}>
            Cancelar (Esc)
          </button>
          <button className="btn primary" disabled={sending || !form.problema.trim()}>
            Armar la solución →
          </button>
        </div>
      </form>
    </div>
  )
}
