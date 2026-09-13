# API設計: マ券・サイドベット

同期サーバ（Sync）。フェーズ `betting` で有効。

## API一覧

| API-ID | メソッド | パス | 概要 | 主な入力 | 主な出力 | 認証 |
|--------|----------|------|------|----------|----------|------|
| API-BETTING-001 | GET | `/api/sessions/{sessionId}/betting` | ベット状態取得 | sessionId | phase, raceIndex, prompt, stock[], turn, players[] | なし |
| API-BETTING-002 | POST | `/api/sessions/{sessionId}/betting/picks` | 札取得＋表裏確定 | ticketKind, ticketId, face | betting.state | 手番 playerId |
| API-BETTING-003 | PUT | `/api/sessions/{sessionId}/betting/double` | 第3ダブル指定 | ticketInstanceId | betting.state | 本人 playerId |
| API-BETTING-004 | POST | `/api/sessions/{sessionId}/advance` | Enter による進行 | sessionId | phase | Display ローカル |

※ advance は他フェーズと同一パス。フェーズに応じてハンドラ切替。

## WebSocket

接続: `WS /ws/sessions/{sessionId}`

| イベント | 方向 | 概要 | 関連API |
|----------|------|------|---------|
| `betting.state` | Sync → 全クライアント | お題・在庫・手番・各所持札（表裏） | API-BETTING-001〜003 |
| `betting.advanced` | Sync → 全クライアント | `card-seed` への遷移 | API-BETTING-004 |

ペイロード（概念）: `raceIndex`, `prompt`, `stock[]`, `currentPlayerId`, `round`, `picksByPlayer`, `doubleByPlayer`。

## エラー

| 条件 | HTTP | ユーザーへの表示 |
|------|------|------------------|
| 手番以外の pick | 403 | 「あなたの番ではありません」 |
| 在庫0 | 409 | 「この札は残りがありません」 |
| face 未指定 | 400 | 「セーフかリスキーを選んでください」 |
| レース1–2で double | 409 | 「このレースでは使えません」 |
| フェーズ不正 | 409 | 「この操作はできません」 |
| Enter だが未完了 | 409 | 「まだドラフト中です」 |

## OPEN

（なし。未完了 advance=409・force-advance なしを採用）

※ stock 初期値: 4×3 マスコット＋YES/NO 計6（公式 CONTENTS）。payoutFaceValue は設計状態に含めない。
