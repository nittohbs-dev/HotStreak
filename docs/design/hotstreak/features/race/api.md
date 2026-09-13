# API設計: レース進行

進行はサーバ主導の自動進行。クライアントは状態購読が主。Display 演出完了 ack は設けない。

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

（コース座標系は 4×12 で確定。物理14行への切替時に TST を更新）

