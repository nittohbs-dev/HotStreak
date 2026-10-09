# 会場プレイ体験の改善

2026-10-09承認済みの9点を対象とする。feature-id: play-experience。

## 関連一覧

| 種別 | ID | 名前 |
|------|-----|------|
| 画面 | SCR-play-001 | 総合優勝（会場・Phone） |
| 画面 | SCR-play-002 | 最初の参加者の進行ボタン |
| API | API-play-001 | 認証済み進行 |
| CLS | CLS-play-001 | GameSession / Room |
| CLS | CLS-play-002 | Application / Phone live / PayoutView |
| CLS | CLS-play-003 | 会場のRaceView / BettingView |
| CLS | CLS-audio-001, CLS-audio-002 | 音声制御 |
| TBL | — | メモリのみ |

## 受け入れ条件

- REQ-play-001: 最終配当→総合優勝→ロビーを同期。最初の人間参加者だけPhoneから進行可能。
- REQ-play-002: 看板、スタート線、名前と状態、カード原画、緑カード補足を修正。
- REQ-play-003: BGM停止時の復帰、音声障害の可視化、実画面サイズでの全画面表示。

既存機能のルールは維持し、本機能の変更箇所は本ディレクトリを正本とする。
