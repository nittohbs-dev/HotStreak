# API設計: 会場プレイ体験

| API-ID | メソッド | パス | 概要 | 主な入力 | 主な出力 | 認証 |
|--------|----------|------|------|----------|----------|------|
| API-play-001 | POST | `/api/sessions/{sid}/advance` | 既存APIの進行権限拡張 | revision, phase, Idempotency-Key | 最新snapshot | Displayローカルトークン、または最初の参加者Cookie |

snapshotにhostPlayerId、canAdvance、advanceLabel、advanceReasonを追加。canAdvanceは進行役本人かつ進行可能条件のときだけtrue。未参加者・一般参加者はfalse。champion snapshotはpayoutと同じbalances/winnersを持つ。phase通知の接頭辞championを追加する。第3payoutの次はchampion、その次にlobby。

既存 /advance のPhoneからのrace直接進行は403。レース操作は API-play-002 経由で会場へ中継。進行条件未成立・古いrevisionは409。CookieはHttpOnly・SameSite=strictを維持する。Displayトークンを一般snapshotに載せない。認証後に冪等性を処理し、リセット後の古いCookieに権限を残さない。


| API-ID | メソッド | パス | 概要 | 主な入力 | 主な出力 | 認証 |
|--------|----------|------|------|----------|----------|------|
| API-play-002 | POST | `/api/sessions/{sid}/enter` | Phone ENTER（非レースは進行、レースは中継） | revision, phase, action=tap/hold, Idempotency-Key | snapshot | 最初の参加者Cookie |
| API-play-003 | POST | `/api/sessions/{sid}/enter/poll` | 中継取得・操作状態報告 | revision, control（canTap, canHold, autoRunning, notice） | snapshot, remoteEnter | Displayローカルトークン |

snapshotのenterControlは会場の操作可否を共有する。PhoneへのremoteEnter・Displayトークンの公開は禁止。入力に同じphase/revision/raceIndexを記録し、配信時にも照合する。Display接続期限・操作可否はサーバで検証する。操作状態だけの変化はゲームrevisionを進めず通知し、Phoneは同一revisionのポーリングでも操作部だけを更新する。
