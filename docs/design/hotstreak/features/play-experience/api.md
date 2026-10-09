# API設計: 会場プレイ体験

| API-ID | メソッド | パス | 概要 | 主な入力 | 主な出力 | 認証 |
|--------|----------|------|------|----------|----------|------|
| API-play-001 | POST | `/api/sessions/{sid}/advance` | 既存APIの進行権限拡張 | revision, phase, Idempotency-Key | 最新snapshot | Displayローカルトークン、または最初の参加者Cookie |

snapshotにhostPlayerId、canAdvance、advanceLabel、advanceReasonを追加。canAdvanceは進行役本人かつ進行可能条件のときだけtrue。未参加者・一般参加者はfalse。champion snapshotはpayoutと同じbalances/winnersを持つ。phase通知の接頭辞championを追加する。第3payoutの次はchampion、その次にlobby。

Phoneからのrace進行は403。進行条件未成立・古いrevisionは409。CookieはHttpOnly・SameSite=strictを維持する。Displayトークンを一般snapshotに載せない。認証後に冪等性を処理し、リセット後の古いCookieに権限を残さない。
