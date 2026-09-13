import type { OutlineFeature } from './types'

type Props = {
  features: OutlineFeature[]
  selectedFeatures: Set<string>
  selectedNodeId: string | null
  search: string
  onToggleFeature: (featureId: string) => void
  onSelectNode: (nodeId: string) => void
  onClose?: () => void
}

export function OutlinePanel({
  features,
  selectedFeatures,
  selectedNodeId,
  search,
  onToggleFeature,
  onSelectNode,
  onClose,
}: Props) {
  const q = search.trim().toLowerCase()

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
      <p className="muted outline-hint">機能を複数選択して関係を表示</p>
      <ul className="outline-tree">
        {features.map((f) => {
          const featureMatch =
            !q ||
            f.id.toLowerCase().includes(q) ||
            f.name.toLowerCase().includes(q)
          const filteredClasses = f.classes
            .map((c) => {
              const classMatch =
                !q ||
                c.id.toLowerCase().includes(q) ||
                c.name.toLowerCase().includes(q)
              const tables = c.tables.filter(
                (t) =>
                  !q ||
                  t.id.toLowerCase().includes(q) ||
                  t.name.toLowerCase().includes(q),
              )
              if (!featureMatch && !classMatch && tables.length === 0) return null
              return { ...c, tables: classMatch || featureMatch ? c.tables : tables }
            })
            .filter(Boolean) as OutlineFeature['classes']

          if (!featureMatch && filteredClasses.length === 0) return null

          return (
            <li key={f.id} className="outline-feature">
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
                    selectedNodeId === f.nodeId ? 'outline-link active' : 'outline-link'
                  }
                  onClick={() => onSelectNode(f.nodeId)}
                >
                  {f.name}
                  <span className="muted"> {f.id}</span>
                </button>
              </div>
              <ul>
                {filteredClasses.map((c) => (
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
                    {c.tables.length > 0 && (
                      <ul>
                        {c.tables.map((t) => (
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
                    )}
                  </li>
                ))}
              </ul>
            </li>
          )
        })}
      </ul>
    </aside>
  )
}
