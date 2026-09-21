# API設計: レース進行

めくるタイミングは会場DisplayのEnter。1押下で1枚を要求し、効果解決はサーバが担当する（2026-09-21ユーザー指示）。Display演出完了ackとは別の操作。現時点のモックはローカル固定データのみ。Enter要求の通信契約・重複排除は同期側の設計時に確定する。

## API一覧

| API-ID | メソッド | パス | 概要 | 主な入力 | 主な出力 | 認証 |
|--------|----------|------|------|----------|----------|------|
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

- Enterによる1枚めくり要求の通信契約は未定。既存GETは状態取得専用のまま。

（コース座標系は 4×12 で確定。物理14行への切替時に TST を更新）

