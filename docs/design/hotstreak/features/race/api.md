# API設計: レース進行

自動進行ON/OFFは会場Displayのローカル状態。新しい切替APIは作らない。DisplayはEnterでONになった後、既存advance APIで1枚ずつ要求する。サーバが効果と終了を判定し、Displayが演出完了まで次の要求を待つ。

## API一覧

| API-ID | メソッド | パス | 概要 | 主な入力 | 主な出力 | 認証 |
|--------|----------|------|------|----------|----------|------|
| API-RACE-002 | POST | `/api/sessions/{sessionId}/advance` | 既存の1枚進行要求 | phase=race, revision | 最新セッション状態 | X-Display-Token, Idempotency-Key |
| API-RACE-001 | GET | `/api/sessions/{sessionId}/race` | レース状態取得 | sessionId | phase, mascots[], course, currentCard, standingsPreview, myBets | なし（myBets は playerId） |

## WebSocket

| イベント | 方向 | 概要 |
|----------|------|------|
| `race.state` | Sync → 全 | 位置・今回のカード（effectKind）・短縮・DQ |
| `race.finished` | Sync → 全 | 着順・sideBetOutcome・phase=payout |

## エラー

| 条件 | HTTP | 表示 |
|------|------|------|
| フェーズ不正 | 409 | 「レース中ではありません」 |

## OPEN

なし。進行要求は実装済みの共通advanceを使用する。

## API-RACE-002: 1枚進行要求

- 新規エンドポイントの追加ではなく、既存advanceのレース用途を記載する。
- リクエストは最新状態の phase=race と revision を含み、X-Display-Token と操作ごとに一意な Idempotency-Key を送る。
- ON/OFFの切替自体は送信しない。未完了の進行要求は最大1件。サーバ応答と演出完了を待って次の要求を作る。
- 停止操作と次の要求が同一フレームなら、Enterを先に処理して新規要求を抑止する。送信済み要求は取り消さず、応答を表示する。
- 通信エラーや409時は自動進行をOFFにし、既存の状態取得で同期する。成否不明の操作を新しいキーで自動再送しない。
- ON/OFFをWS配信・永続化しない。Phoneへの状態通知とサーバ側の効果判定は既存契約を維持する。

（コース座標系は、キャラクターの開始位置を含む4×13マス＋GOAL。STARTは列2、★は列2・7・12、ゴール境界は13）
