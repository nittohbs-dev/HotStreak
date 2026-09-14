export type NodeKind = 'Feature' | 'ClassCommon' | 'ClassFeature' | 'Table' | 'Api'

export type SnapshotNodeData = {
  kind: NodeKind
  label: string
  subLabel: string
  reqCount?: number
  layer?: string
  featureIds?: string[]
  implemented?: boolean
  placeholder?: boolean
  projectId?: string
  guideHeight?: number
}

export type SnapshotEdgeData = {
  kind?: 'uses' | 'inherits'
  projectId?: string
}

export type ProjectSummary = {
  id: string
  title: string
  status: string
  featureCount: number
  classCount: number
  tableCount: number
  gapCount?: number
}

export type MethodRow = {
  メソッド?: string
  引数?: string
  戻り値?: string
  概要?: string
}

export type Snapshot = {
  generatedAt: string
  empty: boolean
  gapCount: number
  scannedFileCount: number
  projects: ProjectSummary[]
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
    data?: SnapshotEdgeData
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
  apis?: Array<Record<string, string> & {
    requestJson?: string | null
    responseJson?: string | null
    bodySummary?: string
    featureId?: string
  }>
  classIds?: string[]
  layer?: string
  responsibility?: string
  relatedTbl?: string[]
  relatedApis?: string[]
  features?: string[]
  columns?: Array<Record<string, string>>
  classes?: string[]
  sourceHits?: Array<{ id: string; file: string }>
  common?: boolean
  projectId?: string
  inheritsFrom?: string | null
  inheritsTo?: string[]
  methods?: MethodRow[]
  requestJson?: string | null
  responseJson?: string | null
  bodySummary?: string
  featureId?: string
  'メソッド'?: string
  'パス'?: string
  '概要'?: string
  '主な入力'?: string
  '主な出力'?: string
  '認証'?: string
  'API-ID'?: string
}

export type LayerFilter = 'all' | 'feature' | 'class' | 'api' | 'db'

export type MobileDrawer = 'none' | 'outline' | 'inspector'

export type OutlineItem = {
  id: string
  name: string
  nodeId: string
}

export type OutlineModel = {
  features: OutlineItem[]
  layers: Array<{ name: string; items: OutlineItem[] }>
  apis: OutlineItem[]
  tables: OutlineItem[]
}
