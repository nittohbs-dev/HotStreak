import type { DetailPayload, SnapshotNodeData } from './types'

type Props = {
  nodeId: string | null
  data: SnapshotNodeData | null
  detail: DetailPayload | null
  projectId: string | null
  onNavigate: (nodeId: string) => void
  onClose?: () => void
}

function JumpList({
  items,
  toNodeId,
  onNavigate,
}: {
  items: string[]
  toNodeId: (localId: string) => string
  onNavigate: (nodeId: string) => void
}) {
  if (!items.length) return <p className="muted">なし</p>
  return (
    <ul>
      {items.map((id) => (
        <li key={id}>
          <button
            type="button"
            className="jump-link"
            onClick={() => onNavigate(toNodeId(id))}
          >
            {id}
          </button>
        </li>
      ))}
    </ul>
  )
}

function JsonBlock({ title, value }: { title: string; value?: string | null }) {
  return (
    <>
      <h3>{title}</h3>
      {value ? <pre className="json-block">{value}</pre> : <p className="muted">未記載</p>}
    </>
  )
}

export function InspectorPanel({
  nodeId,
  data,
  detail,
  projectId,
  onNavigate,
  onClose,
}: Props) {
  const pid = projectId || data?.projectId || detail?.projectId || ''

  if (!nodeId || !data) {
    return (
      <aside className="inspector">
        <div className="outline-header">
          <h2>インスペクタ</h2>
          {onClose && (
            <button type="button" className="drawer-close" onClick={onClose}>
              閉じる
            </button>
          )}
        </div>
        <p className="muted">ノードを選択すると詳細が表示されます。</p>
      </aside>
    )
  }

  return (
    <aside className="inspector">
      <div className="outline-header">
        <h2>{data.label}</h2>
        {onClose && (
          <button type="button" className="drawer-close" onClick={onClose}>
            閉じる
          </button>
        )}
      </div>
      <p className="muted">
        {data.subLabel} · {data.kind}
      </p>

      {data.kind === 'Feature' && detail && (
        <>
          {detail.status && <p>状態: {detail.status}</p>}
          {detail.summary && (
            <>
              <h3>概要</h3>
              <p>{detail.summary}</p>
            </>
          )}
          <h3>要件</h3>
          {(detail.reqs ?? []).length === 0 && <p className="muted">なし</p>}
          <ul>
            {(detail.reqs ?? []).map((r) => (
              <li key={r.id}>
                <strong>{r.id}</strong> {r.title}
              </li>
            ))}
          </ul>
          <h3>画面ワイヤー</h3>
          {(detail.wires ?? []).map((w) => (
            <div key={w.id} className="wire-block">
              <div>
                {w.id}: {w.name}
              </div>
              {w.wire ? <pre>{w.wire}</pre> : <p className="muted">ワイヤーなし</p>}
            </div>
          ))}
          <h3>API</h3>
          {(detail.apis ?? []).length === 0 && <p className="muted">なし</p>}
          <ul>
            {(detail.apis ?? []).map((a) => {
              const apiId = a['API-ID'] || a.id
              return (
                <li key={apiId}>
                  <button
                    type="button"
                    className="jump-link"
                    onClick={() => onNavigate(`${pid}:api:${apiId}`)}
                  >
                    {apiId}
                  </button>{' '}
                  {a['メソッド']} {a['パス']}
                </li>
              )
            })}
          </ul>
          <h3>関連クラス</h3>
          <JumpList
            items={detail.classIds ?? []}
            toNodeId={(id) => `${pid}:class:${id}`}
            onNavigate={onNavigate}
          />
        </>
      )}

      {(data.kind === 'ClassCommon' || data.kind === 'ClassFeature') && detail && (
        <>
          <h3>概要</h3>
          <p>{detail.responsibility || '未記載'}</p>
          <p>層: {detail.layer || '—'}</p>
          <h3>メソッド</h3>
          {(detail.methods ?? []).length === 0 ? (
            <p className="muted">未記載</p>
          ) : (
            <table className="col-table">
              <thead>
                <tr>
                  <th>メソッド</th>
                  <th>引数</th>
                  <th>戻り値</th>
                  <th>概要</th>
                </tr>
              </thead>
              <tbody>
                {(detail.methods ?? []).map((m, i) => (
                  <tr key={`${m['メソッド']}-${i}`}>
                    <td>{m['メソッド']}</td>
                    <td>
                      <code>{m['引数']}</code>
                    </td>
                    <td>
                      <code>{m['戻り値']}</code>
                    </td>
                    <td>{m['概要']}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
          <h3>継承元</h3>
          {detail.inheritsFrom ? (
            <JumpList
              items={[detail.inheritsFrom]}
              toNodeId={(id) => `${pid}:class:${id}`}
              onNavigate={onNavigate}
            />
          ) : (
            <p className="muted">なし</p>
          )}
          <h3>継承先</h3>
          <JumpList
            items={detail.inheritsTo ?? []}
            toNodeId={(id) => `${pid}:class:${id}`}
            onNavigate={onNavigate}
          />
          <h3>使う機能</h3>
          <JumpList
            items={detail.features ?? []}
            toNodeId={(id) => `${pid}:feature:${id}`}
            onNavigate={onNavigate}
          />
          <h3>関連API</h3>
          <JumpList
            items={detail.relatedApis ?? []}
            toNodeId={(id) => `${pid}:api:${id}`}
            onNavigate={onNavigate}
          />
          <h3>関連テーブル</h3>
          <JumpList
            items={detail.relatedTbl ?? []}
            toNodeId={(id) => `${pid}:table:${id}`}
            onNavigate={onNavigate}
          />
        </>
      )}

      {data.kind === 'Api' && detail && (
        <>
          <h3>概要</h3>
          <p>{detail['概要'] || detail.bodySummary || detail.name || '未記載'}</p>
          <p>
            {detail['メソッド']} {detail['パス']}
          </p>
          <p>認証: {detail['認証'] || '—'}</p>
          <p>主な入力: {detail['主な入力'] || '—'}</p>
          <p>主な出力: {detail['主な出力'] || '—'}</p>
          <JsonBlock title="リクエスト JSON" value={detail.requestJson} />
          <JsonBlock title="レスポンス JSON" value={detail.responseJson} />
          {detail.featureId && (
            <>
              <h3>機能</h3>
              <JumpList
                items={[detail.featureId]}
                toNodeId={(id) => `${pid}:feature:${id}`}
                onNavigate={onNavigate}
              />
            </>
          )}
        </>
      )}

      {data.kind === 'Table' && detail && (
        <>
          <h3>カラム</h3>
          {(detail.columns ?? []).length === 0 && <p className="muted">なし</p>}
          <table className="col-table">
            <thead>
              <tr>
                <th>カラム</th>
                <th>型</th>
                <th>必須</th>
              </tr>
            </thead>
            <tbody>
              {(detail.columns ?? []).map((c, i) => (
                <tr key={`${c['カラム']}-${i}`}>
                  <td>{c['カラム']}</td>
                  <td>{c['型']}</td>
                  <td>{c['必須']}</td>
                </tr>
              ))}
            </tbody>
          </table>
          <h3>所有機能</h3>
          <JumpList
            items={detail.features ?? []}
            toNodeId={(id) => `${pid}:feature:${id}`}
            onNavigate={onNavigate}
          />
          <h3>触るクラス</h3>
          <JumpList
            items={detail.classes ?? []}
            toNodeId={(id) => `${pid}:class:${id}`}
            onNavigate={onNavigate}
          />
        </>
      )}

      {data.kind !== 'Api' && (
        <>
          <h3>ソース</h3>
          {(detail?.sourceHits ?? []).length === 0 ? (
            <p className="muted">未検出</p>
          ) : (
            <ul>
              {(detail?.sourceHits ?? []).map((h) => (
                <li key={`${h.id}-${h.file}`}>
                  <code>{h.file}</code>
                </li>
              ))}
            </ul>
          )}
        </>
      )}
    </aside>
  )
}
