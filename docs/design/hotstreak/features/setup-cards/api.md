# API設計: 公開カード準備

同期サーバ（Sync）が提供する REST と WebSocket。lobby 完了後のフェーズ `setup-cards` で有効。

## API一覧

| API-ID | メソッド | パス | 概要 | 主な入力 | 主な出力 | 認証 |
|--------|----------|------|------|----------|----------|------|
| API-SETUP-001 | GET | `/api/sessions/{sessionId}/setup` | 公開カード・配布状態取得 | sessionId | phase, faceUpCards[], dealt, playerCount | なし |
| API-SETUP-002 | POST | `/api/sessions/{sessionId}/advance` | Enter によるフェーズ進行 | sessionId | phase | Display ローカル |

※ 配布自体は `lobby` → `setup-cards` 遷移時に Sync が自動実行する（クライアントからの deal API は設けない）。  
※ advance パスは lobby の API-LOBBY-005 と同一エンドポイント。フェーズに応じて Sync がハンドラを切り替える。

## WebSocket

接続: `WS /ws/sessions/{sessionId}`（lobby と共通）

| イベント | 方向 | 概要 | 関連API |
|----------|------|------|---------|
| `setup.state` | Sync → 全クライアント | 公開カード一覧・配布完了フラグ・phase | 自動配布, API-SETUP-001 |
| `setup.advanced` | Sync → 全クライアント | `betting` への遷移通知 | API-SETUP-002 |

ペイロード（概念）: `sessionId`, `phase`, `faceUpCards[]`（cardId, mascot, effectLabel, lane）, `dealt`（bool）, `handsReady`（playerId ごとの枚数のみ。中身は本人以外に出さない）。

## エラー

| 条件 | HTTP | ユーザーへの表示 |
|------|------|------------------|
| セッション不存在 | 404 | 「セッションが見つかりません」 |
| フェーズが setup-cards 以外で setup 取得 | 409 | 「この操作はできません」 |
| 配布未完了で advance | 409 | 「準備中です」 |
| フェーズ不正で advance | 409 | 「この操作はできません」 |
| カード供給不足 | 500 | 「カードの準備に失敗しました」（再作成を促す） |
