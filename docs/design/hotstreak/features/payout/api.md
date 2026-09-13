# API設計: 配当

## API一覧

| API-ID | メソッド | パス | 概要 | 主な入力 | 主な出力 | 認証 |
|--------|----------|------|------|----------|----------|------|
| API-PAYOUT-001 | GET | `/api/sessions/{sessionId}/payout` | 配当状態 | sessionId | standings, myBreakdown, balances[], raceIndex | playerId 任意 |
| API-PAYOUT-002 | POST | `/api/sessions/{sessionId}/advance` | Enter 進行 | sessionId | phase, raceIndex | Display ローカル |

精算自体は `race.finished` 受信時に Sync が自動実行（クライアントからの settle API は設けない）。

## WebSocket

| イベント | 方向 | 概要 |
|----------|------|------|
| `payout.state` | Sync → 全 | 着順・残高・内訳 |
| `payout.advanced` | Sync → 全 | 次フェーズ（betting または ended） |

## エラー

| 条件 | HTTP | 表示 |
|------|------|------|
| フェーズ不正 | 409 | 「この操作はできません」 |

## OPEN

（なし。同点最多は共同優勝を採用）

※ race3 後 phase=`lobby`。補充は既存 RacingDeck から1枚。breakdown 金額は README 観測確定表（OPEN-payout-002 クローズ済）。
