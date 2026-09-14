import { useMemo, useState, type ReactNode } from 'react'
import type { OutlineModel } from './types'

type Props = {
  model: OutlineModel
  selectedFeatures: Set<string>
  selectedNodeId: string | null
  search: string
  onToggleFeature: (featureId: string) => void
  onSelectNode: (nodeId: string) => void
  onClose?: () => void
}

function Section({
  title,
  open,
  onToggle,
  children,
}: {
  title: string
  open: boolean
  onToggle: () => void
  children: ReactNode
}) {
  return (
    <div className="outline-section">
      <button type="button" className="outline-section-toggle" onClick={onToggle}>
        <span aria-hidden>{open ? '▼' : '▶'}</span> {title}
      </button>
      {open && <div className="outline-section-body">{children}</div>}
    </div>
  )
}

function matchQ(q: string, ...parts: string[]) {
  if (!q) return true
  return parts.some((p) => p.toLowerCase().includes(q))
}

export function OutlinePanel({
  model,
  selectedFeatures,
  selectedNodeId,
  search,
  onToggleFeature,
  onSelectNode,
  onClose,
}: Props) {
  const q = search.trim().toLowerCase()
  const [open, setOpen] = useState<Record<string, boolean>>({})

  const toggle = (key: string) =>
    setOpen((prev) => ({ ...prev, [key]: !prev[key] }))

  const features = model.features.filter((f) => matchQ(q, f.id, f.name))
  const layers = model.layers
    .map((layer) => ({
      ...layer,
      items: layer.items.filter((i) => matchQ(q, i.id, i.name, layer.name)),
    }))
    .filter((l) => l.items.length > 0 || !q)
  const apis = model.apis.filter((a) => matchQ(q, a.id, a.name))
  const tables = model.tables.filter((t) => matchQ(q, t.id, t.name))

  const sectionKeys = useMemo(
    () => [
      'features',
      ...layers.map((l) => `layer:${l.name}`),
      'apis',
      'tables',
    ],
    [layers],
  )

  const closeAllSections = () => {
    const next: Record<string, boolean> = {}
    for (const key of sectionKeys) next[key] = false
    setOpen(next)
  }

  const isOpen = (key: string) => open[key] === true

  return (
    <aside className="outline-panel">
      <div className="outline-header">
        <h2>アウトライン</h2>
        {onClose && (
          <button type="button" className="drawer-close" onClick={onClose}>
            閉じる
          </button>
        )}
      </div>
      <div className="outline-toolbar">
        <p className="muted outline-hint">機能を複数選択／層・エンドポイントで辿る</p>
        <button
          type="button"
          className="outline-collapse-all"
          onClick={closeAllSections}
        >
          セクションを全て閉じる
        </button>
      </div>

      <Section
        title="機能"
        open={isOpen('features')}
        onToggle={() => toggle('features')}
      >
        <ul className="outline-tree">
          {features.map((f) => (
            <li
              key={f.id}
              className={
                selectedFeatures.has(f.id)
                  ? 'outline-feature checked'
                  : 'outline-feature'
              }
            >
              <div className="outline-feature-row">
                <input
                  type="checkbox"
                  checked={selectedFeatures.has(f.id)}
                  onChange={() => onToggleFeature(f.id)}
                  aria-label={`${f.name} を表示`}
                />
                <button
                  type="button"
                  className={
                    selectedNodeId === f.nodeId || selectedFeatures.has(f.id)
                      ? 'outline-link active'
                      : 'outline-link'
                  }
                  onClick={() => onSelectNode(f.nodeId)}
                >
                  {f.name}
                  <span className="muted"> {f.id}</span>
                </button>
              </div>
            </li>
          ))}
        </ul>
      </Section>

      {layers.map((layer) => (
        <Section
          key={layer.name}
          title={layer.name}
          open={isOpen(`layer:${layer.name}`)}
          onToggle={() => toggle(`layer:${layer.name}`)}
        >
          <ul className="outline-tree">
            {layer.items.map((c) => (
              <li key={c.id}>
                <button
                  type="button"
                  className={
                    selectedNodeId === c.nodeId
                      ? 'outline-link active'
                      : 'outline-link'
                  }
                  onClick={() => onSelectNode(c.nodeId)}
                >
                  {c.name}
                  <span className="muted"> {c.id}</span>
                </button>
              </li>
            ))}
          </ul>
        </Section>
      ))}

      <Section
        title="エンドポイント"
        open={isOpen('apis')}
        onToggle={() => toggle('apis')}
      >
        <ul className="outline-tree">
          {apis.length === 0 && <li className="muted">なし</li>}
          {apis.map((a) => (
            <li key={a.id}>
              <button
                type="button"
                className={
                  selectedNodeId === a.nodeId
                    ? 'outline-link active'
                    : 'outline-link'
                }
                onClick={() => onSelectNode(a.nodeId)}
              >
                {a.name}
                <span className="muted"> {a.id}</span>
              </button>
            </li>
          ))}
        </ul>
      </Section>

      <Section
        title="テーブル"
        open={isOpen('tables')}
        onToggle={() => toggle('tables')}
      >
        <ul className="outline-tree">
          {tables.map((t) => (
            <li key={t.id}>
              <button
                type="button"
                className={
                  selectedNodeId === t.nodeId
                    ? 'outline-link active'
                    : 'outline-link'
                }
                onClick={() => onSelectNode(t.nodeId)}
              >
                {t.name}
                <span className="muted"> {t.id}</span>
              </button>
            </li>
          ))}
        </ul>
      </Section>
    </aside>
  )
}
