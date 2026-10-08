import { Background, BackgroundVariant, ReactFlow, ReactFlowProvider, useNodesInitialized, useReactFlow, type Edge, type Node } from '@xyflow/react'
import '@xyflow/react/dist/style.css'
import { BookOpenCheck, Calculator, Cpu, DraftingCompass, FileCheck2, Library, PenLine, Scale, ShieldCheck, UserRound } from 'lucide-react'
import { useEffect, useMemo, useRef } from 'react'
import { ACTOR_META, AGENTS, nodeColor } from '../../agents'
import type { AgentId, FlowNodeId, StageState } from '../../types'
import { FlowEdge, type FlowEdgeData } from './FlowEdge'
import { AgentNode, SubNode, type AgentNodeData, type SubNodeData } from './Nodes'

const nodeTypes = { agent: AgentNode, sub: SubNode }
const edgeTypes = { flow: FlowEdge }

// Fila principal (coordenadas del canvas); el ancho del nodo es 120.
const MAIN: FlowNodeId[] = ['visitante', 'arquitecto', 'financiero', 'riesgo', 'redactor', 'onepager']
const STEP = 290
const xOf = (id: FlowNodeId) => MAIN.indexOf(id) * STEP
const SUB_Y = 250

const ICONS = { visitante: UserRound, arquitecto: DraftingCompass, financiero: Calculator, riesgo: ShieldCheck, redactor: PenLine, onepager: FileCheck2 }

// Herramientas deterministas que usa cada agente (además de su modelo en Foundry)
const TOOLS: Partial<Record<AgentId, { id: string; label: string; caption: string; icon: typeof Cpu }>> = {
  arquitecto: { id: 'tool-catalogo', label: 'Catálogo Azure', caption: 'Herramienta', icon: Library },
  financiero: { id: 'tool-calc', label: 'Calculador', caption: 'Herramienta', icon: Scale },
  riesgo: { id: 'tool-normas', label: 'Normas MX', caption: 'Conocimiento', icon: BookOpenCheck },
}

function buildGraph(s: StageState): { nodes: Node[]; edges: Edge[] } {
  const nodes: Node[] = []
  const edges: Edge[] = []

  for (const id of MAIN) {
    const meta = id === 'onepager' ? { label: 'One-pager', role: 'PDF + QR' } : ACTOR_META[id]
    const data: AgentNodeData = {
      label: meta.label,
      role: meta.role,
      icon: ICONS[id],
      color: nodeColor(id),
      status: s.status[id] ?? 'idle',
      chip: s.chips[id],
      variant: id === 'visitante' ? 'trigger' : id === 'onepager' ? 'output' : 'agent',
    }
    nodes.push({ id, type: 'agent', position: { x: xOf(id), y: 0 }, data, draggable: false, selectable: false })
  }

  // Sub-nodos: modelo de Foundry + herramienta de cada agente
  for (const a of AGENTS) {
    const cx = xOf(a) + 60
    const tool = TOOLS[a]
    const subs = [
      { id: `model-${a}`, label: s.models[a] ?? 'Modelo', caption: 'Modelo · Foundry', icon: Cpu, x: tool ? cx - 72 : cx },
      ...(tool ? [{ ...tool, x: cx + 72 }] : []),
    ]
    for (const sub of subs) {
      const data: SubNodeData = { label: sub.label, caption: sub.caption, icon: sub.icon, color: nodeColor(a), pulse: s.subPulses[sub.id] ?? 0 }
      nodes.push({ id: sub.id, type: 'sub', position: { x: sub.x - 50, y: SUB_Y }, data, draggable: false, selectable: false })
      const edata: FlowEdgeData = { active: (s.subPulses[sub.id] ?? 0) > 0, objection: false, arc: false, sub: true, pulses: s.subPulses[sub.id] ? [s.subPulses[sub.id]] : [] }
      edges.push({ id: `${a}->${sub.id}`, source: a, sourceHandle: 'bottom', target: sub.id, targetHandle: 'in', type: 'flow', data: edata })
    }
  }

  // Cables: el esqueleto del flujo + cada traspaso real (las objeciones vuelven hacia atrás en arco)
  const byKey = new Map<string, Edge>()
  MAIN.slice(1).forEach((to, i) => {
    const from = MAIN[i]
    const data: FlowEdgeData = { active: false, objection: false, arc: false, sub: false, pulses: [] }
    byKey.set(`${from}->${to}`, { id: `${from}->${to}`, source: from, sourceHandle: 'out', target: to, targetHandle: 'in', type: 'flow', data })
  })
  for (const h of s.handoffs) {
    const key = `${h.from}->${h.to}`
    let e = byKey.get(key)
    if (!e) {
      const data: FlowEdgeData = { active: false, objection: h.objection, arc: true, sub: false, pulses: [], label: h.objection ? 'objeción' : undefined }
      e = { id: key, source: h.from, sourceHandle: 'top-out', target: h.to, targetHandle: 'top-in', type: 'flow', data }
      byKey.set(key, e)
    }
    const data = e.data as FlowEdgeData
    e.data = { ...data, active: true, objection: data.objection || h.objection, pulses: [...data.pulses, h.seq] }
  }
  edges.push(...byKey.values())
  return { nodes, edges }
}

const FIT = { padding: { top: 0.2, bottom: 0.04, left: 0.03, right: 0.03 } }

/** Reencuadra el canvas cuando cambia el tamaño del contenedor (pantalla completa, resize, etc.). */
function AutoFit({ container }: { container: React.RefObject<HTMLDivElement | null> }) {
  const { fitView } = useReactFlow()
  const ready = useNodesInitialized()
  useEffect(() => {
    if (!ready || !container.current) return
    fitView(FIT)
    const ro = new ResizeObserver(() => fitView(FIT))
    ro.observe(container.current)
    return () => ro.disconnect()
  }, [ready, fitView, container])
  return null
}

export function FlowCanvas({ s }: { s: StageState }) {
  const { nodes, edges } = useMemo(() => buildGraph(s), [s])
  const ref = useRef<HTMLDivElement>(null)
  return (
    <div ref={ref} className="flow-wrap">
    <ReactFlowProvider>
      <ReactFlow
        nodes={nodes}
        edges={edges}
        nodeTypes={nodeTypes}
        edgeTypes={edgeTypes}
        fitView
        fitViewOptions={FIT}
        minZoom={0.2}
        nodesDraggable={false}
        nodesConnectable={false}
        elementsSelectable={false}
        panOnDrag={false}
        zoomOnScroll={false}
        zoomOnPinch={false}
        zoomOnDoubleClick={false}
        preventScrolling
        colorMode="dark"
      >
        <Background variant={BackgroundVariant.Dots} gap={24} size={1.6} color="var(--grid-dot)" />
        <AutoFit container={ref} />
      </ReactFlow>
    </ReactFlowProvider>
    </div>
  )
}
