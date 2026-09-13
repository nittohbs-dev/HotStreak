import { useCallback, useEffect, useMemo, useRef, useState } from 'react'
import {
  Background,
  BackgroundVariant,
  Controls,
  MiniMap,
  ReactFlow,
  ReactFlowProvider,
  useEdgesState,
  useNodesState,
  useReactFlow,
  type Edge,
  type Node,
  type NodeTypes,
} from '@xyflow/react'
import '@xyflow/react/dist/style.css'
import { InspectorPanel } from './InspectorPanel'
import { OutlinePanel } from './OutlinePanel'
import { ProjectSwitcher } from './ProjectSwitcher'
import {
  ClassCommonNode,
  ClassFeatureNode,
  FeatureNode,
  TableNode,
} from './nodes'
import type {
  LayerFilter,
  MobileDrawer,
  OutlineModel,
  Snapshot,
  SnapshotEdgeData,
  SnapshotNodeData,
} from './types'

const nodeTypes: NodeTypes = {
  feature: FeatureNode,
  classCommon: ClassCommonNode,
  classFeature: ClassFeatureNode,
  table: TableNode,
}

const MOBILE_MQ = '(max-width: 768px)'
const COL_X = { Feature: 40, Class: 360, Table: 700 } as const
const ROW_GAP = 120

function readQuery(): { project: string | null; node: string | null } {
  const params = new URLSearchParams(window.location.search)
  return { project: params.get('project'), node: params.get('node') }
}

function writeQuery(project: string | null, node: string | null) {
  const url = new URL(window.location.href)
  if (project) url.searchParams.set('project', project)
  else url.searchParams.delete('project')
  if (node) url.searchParams.set('node', node)
  else url.searchParams.delete('node')
  window.history.replaceState({}, '', url.toString())
}

function matchesLayer(node: Node, filter: LayerFilter): boolean {
  if (filter === 'all') return true
  const kind = (node.data as SnapshotNodeData).kind
  if (filter === 'feature') return kind === 'Feature'
  if (filter === 'class') return kind === 'ClassCommon' || kind === 'ClassFeature'
  if (filter === 'db') return kind === 'Table'
  return true
}

function matchesSearch(node: Node, search: string): boolean {
  const q = search.trim().toLowerCase()
  if (!q) return true
  const data = node.data as SnapshotNodeData
  return (
    data.label.toLowerCase().includes(q) ||
    data.subLabel.toLowerCase().includes(q) ||
    (data.featureIds ?? []).some((f) => f.toLowerCase().includes(q)) ||
    (data.layer ?? '').toLowerCase().includes(q)
  )
}

function columnOf(kind: SnapshotNodeData['kind']): number {
  if (kind === 'Feature') return COL_X.Feature
  if (kind === 'Table') return COL_X.Table
  return COL_X.Class
}

function CanvasApp() {
  const initial = readQuery()
  const { fitView } = useReactFlow()
  const [snapshot, setSnapshot] = useState<Snapshot | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [filter, setFilter] = useState<LayerFilter>('all')
  const [search, setSearch] = useState('')
  const [gapOnly, setGapOnly] = useState(false)
  const [headerOpen, setHeaderOpen] = useState(false)
  const [isMobile, setIsMobile] = useState(
    () => window.matchMedia(MOBILE_MQ).matches,
  )
  const [drawer, setDrawer] = useState<MobileDrawer>('none')
  const [projectId, setProjectId] = useState<string | null>(initial.project)
  const [selectedFeatures, setSelectedFeatures] = useState<Set<string>>(
    () => new Set(),
  )
  const [selectedId, setSelectedId] = useState<string | null>(initial.node)
  const [nodes, setNodes, onNodesChange] = useNodesState<Node>([])
  const [edges, setEdges, onEdgesChange] = useEdgesState<Edge>([])
  const layoutKeyRef = useRef('')

  useEffect(() => {
    const mq = window.matchMedia(MOBILE_MQ)
    const onChange = () => setIsMobile(mq.matches)
    mq.addEventListener('change', onChange)
    return () => mq.removeEventListener('change', onChange)
  }, [])

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
        const ids = data.projects.map((p) => p.id)
        const nextProject =
          (initial.project && ids.includes(initial.project)
            ? initial.project
            : ids[0]) || null
        setProjectId(nextProject)
        if (
          initial.node &&
          !data.nodes.some((n) => n.id === initial.node) &&
          !data.details[initial.node]
        ) {
          setSelectedId(null)
        }
      })
      .catch((e: Error) => setError(e.message))
    // eslint-disable-next-line react-hooks/exhaustive-deps -- initial URL once
  }, [setNodes, setEdges])

  useEffect(() => {
    writeQuery(projectId, selectedId)
  }, [projectId, selectedId])

  useEffect(() => {
    setSelectedFeatures(new Set())
    setSelectedId((prev) => {
      if (!prev || !projectId) return null
      if (prev.startsWith(`${projectId}:`)) return prev
      return null
    })
  }, [projectId])

  const projectNodes = useMemo(
    () =>
      nodes.filter((n) => {
        const d = n.data as SnapshotNodeData
        if (d.placeholder) return true
        return d.projectId === projectId
      }),
    [nodes, projectId],
  )

  const projectEdges = useMemo(
    () =>
      edges.filter((e) => {
        const d = e.data as SnapshotEdgeData | undefined
        if (d?.projectId) return d.projectId === projectId
        return (
          e.source.startsWith(`${projectId}:`) &&
          e.target.startsWith(`${projectId}:`)
        )
      }),
    [edges, projectId],
  )

  const featureFilteredIds = useMemo(() => {
    if (selectedFeatures.size === 0) {
      return new Set(projectNodes.map((n) => n.id))
    }
    const ids = new Set<string>()
    for (const n of projectNodes) {
      const d = n.data as SnapshotNodeData
      if (d.kind === 'Feature' && selectedFeatures.has(d.subLabel)) {
        ids.add(n.id)
      }
      if (
        (d.kind === 'ClassCommon' || d.kind === 'ClassFeature') &&
        (d.featureIds ?? []).some((f) => selectedFeatures.has(f))
      ) {
        ids.add(n.id)
      }
      if (
        d.kind === 'Table' &&
        (d.featureIds ?? []).some((f) => selectedFeatures.has(f))
      ) {
        ids.add(n.id)
      }
    }
    let changed = true
    while (changed) {
      changed = false
      for (const e of projectEdges) {
        const kind = (e.data as SnapshotEdgeData | undefined)?.kind
        if (kind === 'inherits' && ids.has(e.target) && !ids.has(e.source)) {
          ids.add(e.source)
          changed = true
        }
      }
    }
    return ids
  }, [projectNodes, projectEdges, selectedFeatures])

  const visibilityKey = useMemo(() => {
    const visible = projectNodes
      .filter((n) => {
        const d = n.data as SnapshotNodeData
        return (
          d.placeholder ||
          (featureFilteredIds.has(n.id) &&
            matchesLayer(n, filter) &&
            matchesSearch(n, search) &&
            (!gapOnly || d.implemented === false))
        )
      })
      .map((n) => n.id)
      .sort()
    return `${projectId}|${visible.join(',')}`
  }, [projectNodes, featureFilteredIds, filter, search, gapOnly, projectId])

  useEffect(() => {
    if (!projectId || !nodes.length) return
    if (layoutKeyRef.current === visibilityKey) return
    layoutKeyRef.current = visibilityKey

    const buckets: Record<'Feature' | 'Class' | 'Table', Node[]> = {
      Feature: [],
      Class: [],
      Table: [],
    }
    for (const n of nodes) {
      const d = n.data as SnapshotNodeData
      if (d.projectId && d.projectId !== projectId) continue
      const show =
        d.placeholder ||
        (featureFilteredIds.has(n.id) &&
          matchesLayer(n, filter) &&
          matchesSearch(n, search) &&
          (!gapOnly || d.implemented === false))
      if (!show) continue
      if (d.kind === 'Feature') buckets.Feature.push(n)
      else if (d.kind === 'Table') buckets.Table.push(n)
      else buckets.Class.push(n)
    }

    const pos = new Map<string, { x: number; y: number }>()
    ;(['Feature', 'Class', 'Table'] as const).forEach((bucket) => {
      buckets[bucket].forEach((n, i) => {
        const kind = (n.data as SnapshotNodeData).kind
        pos.set(n.id, { x: columnOf(kind), y: 60 + i * ROW_GAP })
      })
    })

    setNodes((prev) =>
      prev.map((n) => {
        const p = pos.get(n.id)
        if (!p) return n
        return { ...n, position: p }
      }),
    )

    requestAnimationFrame(() => {
      fitView({ padding: 0.2, duration: 200 })
    })
  }, [
    visibilityKey,
    projectId,
    nodes.length,
    featureFilteredIds,
    filter,
    search,
    gapOnly,
    setNodes,
    fitView,
  ])

  const visibleNodes = useMemo(
    () =>
      projectNodes.map((n) => {
        const d = n.data as SnapshotNodeData
        const show =
          d.placeholder ||
          (featureFilteredIds.has(n.id) &&
            matchesLayer(n, filter) &&
            matchesSearch(n, search) &&
            (!gapOnly || d.implemented === false))
        return { ...n, hidden: !show }
      }),
    [projectNodes, featureFilteredIds, filter, search, gapOnly],
  )

  const outlineModel: OutlineModel = useMemo(() => {
    if (!projectId || !snapshot) {
      return { features: [], layers: [], apis: [], tables: [] }
    }
    const features = projectNodes
      .filter((n) => {
        const d = n.data as SnapshotNodeData
        return d.kind === 'Feature' && !d.placeholder
      })
      .map((n) => {
        const d = n.data as SnapshotNodeData
        return { id: d.subLabel, name: d.label, nodeId: n.id }
      })

    const layerMap = new Map<string, OutlineModel['layers'][0]['items']>()
    for (const n of projectNodes) {
      const d = n.data as SnapshotNodeData
      if (d.kind !== 'ClassCommon' && d.kind !== 'ClassFeature') continue
      if (selectedFeatures.size > 0 && !featureFilteredIds.has(n.id)) continue
      const layer = d.layer || '（層未設定）'
      const list = layerMap.get(layer) || []
      list.push({ id: d.subLabel, name: d.label, nodeId: n.id })
      layerMap.set(layer, list)
    }

    const apis: OutlineModel['apis'] = []
    for (const [id, detail] of Object.entries(snapshot.details)) {
      if (!id.startsWith(`${projectId}:api:`)) continue
      if (
        selectedFeatures.size > 0 &&
        detail.featureId &&
        !selectedFeatures.has(detail.featureId)
      ) {
        continue
      }
      apis.push({
        id: detail.id || detail['API-ID'] || id.split(':').pop() || id,
        name: detail.name || detail['概要'] || detail.id || id,
        nodeId: id,
      })
    }

    const tables = projectNodes
      .filter((n) => (n.data as SnapshotNodeData).kind === 'Table')
      .filter((n) => selectedFeatures.size === 0 || featureFilteredIds.has(n.id))
      .map((n) => {
        const d = n.data as SnapshotNodeData
        return { id: d.subLabel, name: d.label, nodeId: n.id }
      })

    return {
      features,
      layers: [...layerMap.entries()].map(([name, items]) => ({ name, items })),
      apis,
      tables,
    }
  }, [
    projectId,
    snapshot,
    projectNodes,
    selectedFeatures,
    featureFilteredIds,
  ])

  const relatedIds = useMemo(() => {
    if (!selectedId) return new Set<string>()
    const set = new Set<string>([selectedId])
    for (const e of projectEdges) {
      if (e.source === selectedId) set.add(e.target)
      if (e.target === selectedId) set.add(e.source)
    }
    return set
  }, [selectedId, projectEdges])

  const styledEdges = useMemo(
    () =>
      projectEdges.map((e) => {
        const src = projectNodes.find((n) => n.id === e.source)
        const tgt = projectNodes.find((n) => n.id === e.target)
        const srcVisible =
          src &&
          featureFilteredIds.has(src.id) &&
          matchesLayer(src, filter) &&
          matchesSearch(src, search) &&
          (!gapOnly ||
            (src.data as SnapshotNodeData).implemented === false)
        const tgtVisible =
          tgt &&
          featureFilteredIds.has(tgt.id) &&
          matchesLayer(tgt, filter) &&
          matchesSearch(tgt, search) &&
          (!gapOnly ||
            (tgt.data as SnapshotNodeData).implemented === false)
        const active =
          selectedId && (e.source === selectedId || e.target === selectedId)
        const inherits =
          (e.data as SnapshotEdgeData | undefined)?.kind === 'inherits'
        return {
          ...e,
          hidden: !srcVisible || !tgtVisible,
          style: {
            stroke: active ? '#7ee0c8' : inherits ? '#8a97ab' : '#4a5568',
            strokeWidth: active ? 2.5 : 1.5,
            strokeDasharray: inherits ? '6 4' : undefined,
          },
          animated: Boolean(active),
        }
      }),
    [
      projectEdges,
      projectNodes,
      featureFilteredIds,
      filter,
      search,
      gapOnly,
      selectedId,
    ],
  )

  const onSelect = useCallback(
    (id: string | null) => {
      setSelectedId(id)
      if (isMobile && id) setDrawer('inspector')
    },
    [isMobile],
  )

  const onToggleFeature = useCallback((fid: string) => {
    setSelectedFeatures((prev) => {
      const next = new Set(prev)
      if (next.has(fid)) next.delete(fid)
      else next.add(fid)
      return next
    })
  }, [])

  const selectedNode = projectNodes.find((n) => n.id === selectedId) || null
  const detail = selectedId && snapshot ? snapshot.details[selectedId] : null
  const selectedData: SnapshotNodeData | null = selectedNode
    ? (selectedNode.data as SnapshotNodeData)
    : selectedId?.includes(':api:') && detail
      ? {
          kind: 'Api',
          label: detail.name || detail['概要'] || detail.id,
          subLabel: detail.id || detail['API-ID'] || selectedId,
          projectId: projectId || undefined,
        }
      : null

  const activeProject = snapshot?.projects.find((p) => p.id === projectId)
  const gapDisplay = activeProject?.gapCount ?? snapshot?.gapCount ?? '—'

  const openDrawer = (next: MobileDrawer) => {
    setDrawer((cur) => (cur === next ? 'none' : next))
  }

  const outlineEl = (
    <OutlinePanel
      model={outlineModel}
      selectedFeatures={selectedFeatures}
      selectedNodeId={selectedId}
      search={search}
      onToggleFeature={onToggleFeature}
      onSelectNode={onSelect}
      onClose={isMobile ? () => setDrawer('none') : undefined}
    />
  )

  const inspectorEl = (
    <InspectorPanel
      nodeId={selectedId}
      data={selectedData}
      detail={detail ?? null}
      projectId={projectId}
      onNavigate={onSelect}
      onClose={isMobile ? () => setDrawer('none') : undefined}
    />
  )

  return (
    <div className="app-shell">
      <header className={`topbar${headerOpen ? ' open' : ''}`}>
        <button
          type="button"
          className="menu-toggle"
          aria-label="フィルタを開く"
          onClick={() => setHeaderOpen((v) => !v)}
        >
          ≡
        </button>
        <div className="brand">Spec Browser</div>
        <ProjectSwitcher
          projects={snapshot?.projects ?? []}
          value={projectId}
          onChange={setProjectId}
        />
        <div className={`topbar-tools${headerOpen ? ' show' : ''}`}>
          <input
            className="search-input"
            type="search"
            placeholder="検索…"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            aria-label="検索"
          />
          <label className="gap-only">
            <input
              type="checkbox"
              checked={gapOnly}
              onChange={(e) => setGapOnly(e.target.checked)}
            />
            ギャップのみ
          </label>
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
        </div>
        <div className="gap">
          ギャップ {gapDisplay}
          <span className="muted">
            {' '}
            · ソース {snapshot?.scannedFileCount ?? 0} ファイル
          </span>
        </div>
      </header>

      <div className={`main${isMobile ? ' mobile' : ''}`}>
        {!isMobile && outlineEl}
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
            <Background
              variant={BackgroundVariant.Dots}
              gap={18}
              size={1}
              color="#2a3344"
            />
            <Controls showInteractive={false} />
            {!isMobile && <MiniMap pannable zoomable />}
          </ReactFlow>
          {isMobile && (
            <div className="mobile-dock">
              <button type="button" onClick={() => openDrawer('outline')}>
                一覧
              </button>
              <button type="button" onClick={() => openDrawer('inspector')}>
                詳細
              </button>
            </div>
          )}
        </div>
        {!isMobile && inspectorEl}
        {isMobile && drawer === 'outline' && (
          <div className="drawer-backdrop" onClick={() => setDrawer('none')}>
            <div className="drawer sheet" onClick={(e) => e.stopPropagation()}>
              {outlineEl}
            </div>
          </div>
        )}
        {isMobile && drawer === 'inspector' && (
          <div className="drawer-backdrop" onClick={() => setDrawer('none')}>
            <div className="drawer sheet" onClick={(e) => e.stopPropagation()}>
              {inspectorEl}
            </div>
          </div>
        )}
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
