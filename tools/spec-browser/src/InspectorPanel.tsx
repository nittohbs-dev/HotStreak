import type { DetailPayload, SnapshotNodeData } from './types'

type Props = {
  nodeId: string | null
  data: SnapshotNodeData | null
  detail: DetailPayload | null
}

export function InspectorPanel({ nodeId, data, detail }: Props) {
  if (!nodeId || !data) {
    return (
      <aside className="inspector">
        <h2>インスペクタ</h2>
        <p className="muted">ノードを選択すると詳細が表示されます。</p>
      </aside>
    )
  }

  return (
    <aside className="inspector">
      <h2>{data.label}</h2>
      <p className="muted">
        {data.subLabel} · {data.kind}
      </p>

      {data.kind === 'Feature' && detail && (
        <>
          {detail.status && <p>状態: {detail.status}</p>}
          {detail.summary && <p>{detail.summary}</p>}
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
            {(detail.apis ?? []).map((a) => (
              <li key={a['API-ID']}>
                {a['API-ID']} {a['メソッド']} {a['パス']}
              </li>
            ))}
          </ul>
          <h3>関連クラス</h3>
          <ul>
            {(detail.classIds ?? []).map((id) => (
              <li key={id}>{id}</li>
            ))}
          </ul>
        </>
      )}

      {(data.kind === 'ClassCommon' || data.kind === 'ClassFeature') && detail && (
        <>
          <p>{detail.responsibility || '責務未記載'}</p>
          <p>層: {detail.layer || '—'}</p>
          <h3>使う機能</h3>
          <ul>
            {(detail.features ?? []).map((f) => (
              <li key={f}>{f}</li>
            ))}
          </ul>
          <h3>関連テーブル</h3>
          <ul>
            {(detail.relatedTbl ?? []).map((t) => (
              <li key={t}>{t}</li>
            ))}
          </ul>
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
          <ul>
            {(detail.features ?? []).map((f) => (
              <li key={f}>{f}</li>
            ))}
          </ul>
          <h3>触るクラス</h3>
          <ul>
            {(detail.classes ?? []).map((c) => (
              <li key={c}>{c}</li>
            ))}
          </ul>
        </>
      )}

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
    </aside>
  )
}
