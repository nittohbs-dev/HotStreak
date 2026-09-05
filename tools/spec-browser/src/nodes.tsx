import { memo } from 'react'
import { Handle, Position, type NodeProps } from '@xyflow/react'
import type { SnapshotNodeData } from './types'

function Badge({ ok }: { ok?: boolean }) {
  if (ok) return <span className="node-badge ok" title="ソース照合あり">✓</span>
  return <span className="node-badge miss" title="ソース未検出">!</span>
}

function SpecNode({
  data,
  colorClass,
}: {
  data: SnapshotNodeData
  colorClass: string
}) {
  return (
    <div className={`spec-node ${colorClass}`}>
      {!data.placeholder && <Badge ok={data.implemented} />}
      <Handle type="target" position={Position.Left} />
      <div className="spec-node-title">{data.label}</div>
      <div className="spec-node-sub">{data.subLabel}</div>
      {data.kind === 'Feature' && !data.placeholder && (
        <div className="spec-node-meta">REQ {data.reqCount ?? 0}</div>
      )}
      {(data.kind === 'ClassCommon' || data.kind === 'ClassFeature') && (
        <div className="spec-node-meta">
          {data.kind === 'ClassCommon' ? '共通' : '固有'}
          {data.layer ? ` · ${data.layer}` : ''}
        </div>
      )}
      <Handle type="source" position={Position.Right} />
    </div>
  )
}

export const FeatureNode = memo(function FeatureNode({
  data,
}: NodeProps & { data: SnapshotNodeData }) {
  return <SpecNode data={data} colorClass="feature" />
})

export const ClassCommonNode = memo(function ClassCommonNode({
  data,
}: NodeProps & { data: SnapshotNodeData }) {
  return <SpecNode data={data} colorClass="class-common" />
})

export const ClassFeatureNode = memo(function ClassFeatureNode({
  data,
}: NodeProps & { data: SnapshotNodeData }) {
  return <SpecNode data={data} colorClass="class-feature" />
})

export const TableNode = memo(function TableNode({
  data,
}: NodeProps & { data: SnapshotNodeData }) {
  return <SpecNode data={data} colorClass="table" />
})
