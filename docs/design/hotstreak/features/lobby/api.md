# API設計: 参加・ロビー

同期サーバ（Sync）が提供する REST と WebSocket。Phone・Display は同一セッション ID で接続する。

## API一覧

| API-ID | メソッド | パス | 概要 | 主な入力 | 主な出力 | 認証 |
|--------|----------|------|------|----------|----------|------|
| API-LOBBY-001 | POST | `/api/sessions` | セッション作成（Display 起動時） | （なし） | sessionId, joinUrl, phase | Display ローカル |
| API-LOBBY-002 | GET | `/api/sessions/{sessionId}` | ロビー状態取得 | sessionId | phase, players[], playerCount | なし |
| API-LOBBY-003 | POST | `/api/sessions/{sessionId}/join` | Phone 参加 | sessionId | playerId, phase, players[] | なし |
| API-LOBBY-004 | PUT | `/api/sessions/{sessionId}/players/{playerId}/name` | 名前確定 | displayName（非空） | player, players[] | playerId 一致 |
| API-LOBBY-005 | POST | `/api/sessions/{sessionId}/advance` | Enter によるフェーズ進行 | sessionId | phase, players[] | Display ローカル |

## WebSocket

接続: `WS /ws/sessions/{sessionId}`

| イベント | 方向 | 概要 | 関連API |
|----------|------|------|---------|
| `lobby.state` | Sync → 全クライアント | 参加者一覧・人数・各 player の nameReady・phase | API-LOBBY-003, 004, 005 |
| `lobby.advanced` | Sync → 全クライアント | `setup-cards` への遷移通知 | API-LOBBY-005 |

ペイロード（概念）: `sessionId`, `phase`, `players[]`（playerId, displayName, nameReady, balance）。

## エラー

| 条件 | HTTP | ユーザーへの表示 |
|------|------|------------------|
| セッション不存在 | 404 | 「セッションが見つかりません」 |
| ロビー満員（9人目以降） | 409 | 「参加人数が上限です」 |
| ロビー終了後の join | 409 | 「受付は終了しました」 |
| 空の表示名 | 400 | 「名前を入力してください」 |
| 他人の playerId で名前変更 | 403 | 「操作できません」 |
| 3人未満で advance | 409 | 「参加者が足りません（3人以上）」 |
| フェーズ不正（lobby 以外で advance） | 409 | 「この操作はできません」 |
