# API設計: カード仕込み

## API一覧

| API-ID | メソッド | パス | 概要 | 主な入力 | 主な出力 | 認証 |
|--------|----------|------|------|----------|----------|------|
| API-SEED-001 | GET | `/api/sessions/{sessionId}/seed` | 仕込み状態 | sessionId | phase, progress[], deckCountExpected, hand[]（本人のみ） | playerId 任意 |
| API-SEED-002 | POST | `/api/sessions/{sessionId}/seed` | 手札1枚仕込み | handCardId | seed.state | 本人 |
| API-SEED-003 | POST | `/api/sessions/{sessionId}/advance` | Enter 進行 | sessionId | phase | Display ローカル |

## WebSocket

| イベント | 方向 | 概要 | 関連API |
|----------|------|------|---------|
| `seed.state` | Sync → 全 | 進捗・見込み枚数（手札中身は含めない） | API-SEED-001, 002 |
| `seed.advanced` | Sync → 全 | `race` へ | API-SEED-003 |

## エラー

| 条件 | HTTP | 表示 |
|------|------|------|
| 手札に無い cardId | 400 | 「そのカードは選べません」 |
| 既に仕込み済 | 409 | 「すでに仕込んでいます」 |
| 未仕込みありで Enter | 409 | 「まだ仕込み中です」 |
| デッキ枚数不一致 | 500 | 「デッキの準備に失敗しました」 |
| フェーズ不正 | 409 | 「この操作はできません」 |

## OPEN

（なし。未仕込み advance=409・force-advance なしを採用）

※ 仕込み取消 API は設けない（確定後変更不可）。
