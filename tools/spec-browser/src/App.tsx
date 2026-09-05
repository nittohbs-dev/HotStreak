import { useCallback, useEffect, useMemo, useState } from 'react'
import {
  Background,
  BackgroundVariant,
  Controls,
  MiniMap,
  ReactFlow,
  ReactFlowProvider,
  useEdgesState,
  useNodesState,
  type Edge,
  type Node,
  type NodeTypes,
} from '@xyflow/react'
import '@xyflow/react/dist/style.css'
import { InspectorPanel } from './InspectorPanel'
import {
  ClassCommonNode,
  ClassFeatureNode,
  FeatureNode,
  TableNode,
} from './nodes'
import type { LayerFilter, Snapshot, SnapshotNodeData } from './types'

const nodeTypes: NodeTypes = {
  feature: FeatureNode,
  classCommon: ClassCommonNode,
  classFeature: ClassFeatureNode,
  table: TableNode,
}

function readQueryNode(): string | null {
  const params = new URLSearchParams(window.location.search)
  return params.get('node')
}

function writeQueryNode(id: string | null) {
  const url = new URL(window.location.href)
  if (id) url.searchParams.set('node', id)
  else url.searchParams.delete('node')
  window.history.replaceState({}, '', url.toString())
}

function matchesFilter(node: Node, filter: LayerFilter): boolean {
  if (filter === 'all') return true
  const kind = (node.data as SnapshotNodeData).kind
  if (filter === 'feature') return kind === 'Feature'
  if (filter === 'class') return kind === 'ClassCommon' || kind === 'ClassFeature'
  if (filter === 'db') return kind === 'Table'
  return true
}

function CanvasApp() {
  const [snapshot, setSnapshot] = useState<Snapshot | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [filter, setFilter] = useState<LayerFilter>('all')
  const [selectedId, setSelectedId] = useState<string | null>(readQueryNode())
  const [nodes, setNodes, onNodesChange] = useNodesState<Node>([])
  const [edges, setEdges, onEdgesChange] = useEdgesState<Edge>([])

  useEffect(() => {
    const base = import.meta.env.BASE_URL || '/'
    fetch(`${base}snapshot.json`)
      .then(async (res) => {
        if (!res.ok) throw new Error(`snapshot.json HTTP ${res.status}`)
        return res.json() as Promise<Snapshot>
      })
      .then((data) => {
        setSnapshot(data)
        setNodes(data.nodes as Node[])
        setEdges(data.edges as Edge[])
      })
      .catch((e: Error) => setError(e.message))
  }, [setNodes, setEdges])

  const visibleNodes = useMemo(
    () => nodes.map((n) => ({ ...n, hidden: !matchesFilter(n, filter) })),
    [nodes, filter],
  )

  const relatedIds = useMemo(() => {
    if (!selectedId) return new Set<string>()
    const set = new Set<string>([selectedId])
    for (const e of edges) {
      if (e.source === selectedId) set.add(e.target)
      if (e.target === selectedId) set.add(e.source)
    }
    return set
  }, [selectedId, edges])

  const styledEdges = useMemo(
    () =>
      edges.map((e) => {
        const active =
          selectedId && (e.source === selectedId || e.target === selectedId)
        return {
          ...e,
          hidden:
            filter !== 'all' &&
            (!matchesFilter(
              nodes.find((n) => n.id === e.source) || ({ data: {} } as Node),
              filter,
            ) ||
              !matchesFilter(
                nodes.find((n) => n.id === e.target) || ({ data: {} } as Node),
                filter,
              )),
          style: {
            stroke: active ? '#7ee0c8' : '#4a5568',
            strokeWidth: active ? 2.5 : 1.5,
          },
          animated: Boolean(active),
        }
      }),
    [edges, selectedId, filter, nodes],
  )

  const onSelect = useCallback((id: string | null) => {
    setSelectedId(id)
    writeQueryNode(id)
  }, [])

  const selectedNode = nodes.find((n) => n.id === selectedId) || null
  const selectedData = (selectedNode?.data as SnapshotNodeData) || null
  const detail = selectedId && snapshot ? snapshot.details[selectedId] : null

  return (
    <div className="app-shell">
      <header className="topbar">
        <div className="brand">Spec Browser</div>
        <div className="filters" role="group" aria-label="層フィルタ">
          {(
            [
              ['all', '全部'],
              ['feature', '機能'],
              ['class', 'クラス'],
              ['db', 'DB'],
            ] as const
          ).map(([id, label]) => (
            <button
              key={id}
              type="button"
              className={filter === id ? 'active' : ''}
              onClick={() => setFilter(id)}
            >
              {label}
            </button>
          ))}
        </div>
        <div className="gap">
          ギャップ {snapshot?.gapCount ?? '—'}
          <span className="muted">
            {' '}
            · ソース {snapshot?.scannedFileCount ?? 0} ファイル
          </span>
        </div>
      </header>

      <div className="main">
        <div className="canvas-wrap">
          {error && <div className="banner error">{error}</div>}
          {!error && !snapshot && <div className="banner">読込中…</div>}
          <ReactFlow
            nodes={visibleNodes.map((n) => ({
              ...n,
              selected: n.id === selectedId,
              style: {
                opacity: selectedId && !relatedIds.has(n.id) ? 0.45 : 1,
              },
            }))}
            edges={styledEdges}
            onNodesChange={onNodesChange}
            onEdgesChange={onEdgesChange}
            nodeTypes={nodeTypes}
            nodesDraggable={false}
            nodesConnectable={false}
            elementsSelectable
            onNodeClick={(_, node) => onSelect(node.id)}
            onNodeDoubleClick={(_, node) => onSelect(node.id)}
            onPaneClick={() => onSelect(null)}
            fitView
            minZoom={0.2}
            proOptions={{ hideAttribution: true }}
          >
            <Background variant={BackgroundVariant.Dots} gap={18} size={1} color="#2a3344" />
            <Controls showInteractive={false} />
            <MiniMap pannable zoomable />
          </ReactFlow>
        </div>
        <InspectorPanel
          nodeId={selectedId}
          data={selectedData}
          detail={detail ?? null}
        />
      </div>
    </div>
  )
}

export default function App() {
  return (
    <ReactFlowProvider>
      <CanvasApp />
    </ReactFlowProvider>
  )
}
