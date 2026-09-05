export type NodeKind = 'Feature' | 'ClassCommon' | 'ClassFeature' | 'Table'

export type SnapshotNodeData = {
  kind: NodeKind
  label: string
  subLabel: string
  reqCount?: number
  layer?: string
  featureIds?: string[]
  implemented?: boolean
  placeholder?: boolean
}

export type Snapshot = {
  generatedAt: string
  empty: boolean
  gapCount: number
  scannedFileCount: number
  projects: Array<{
    id: string
    title: string
    status: string
    featureCount: number
    classCount: number
    tableCount: number
  }>
  nodes: Array<{
    id: string
    type: string
    position: { x: number; y: number }
    data: SnapshotNodeData
  }>
  edges: Array<{
    id: string
    source: string
    target: string
    type?: string
  }>
  details: Record<string, DetailPayload>
}

export type DetailPayload = {
  id: string
  name?: string
  status?: string
  summary?: string
  readme?: string
  reqs?: Array<{ id: string; title: string; body: string }>
  screens?: Array<Record<string, string>>
  wires?: Array<{ id: string; name: string; wire: string }>
  apis?: Array<Record<string, string>>
  classIds?: string[]
  layer?: string
  responsibility?: string
  relatedTbl?: string[]
  features?: string[]
  columns?: Array<Record<string, string>>
  classes?: string[]
  sourceHits?: Array<{ id: string; file: string }>
  common?: boolean
}

export type LayerFilter = 'all' | 'feature' | 'class' | 'db'
