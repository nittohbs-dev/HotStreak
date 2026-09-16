# マ券ドラフト画面（Issue #32）

SCR-phone-002 / REQ-betting-001〜006（スマホ側）。
スネークドラフトで札を1枚選び、セーフ／リスキーを決めて確定します。第3レースのみ所持2枚から1枚をダブル指定します。
同期サーバ・Display 画面・ロビー・カード仕込みは含みません。

## 技術

素の HTML / CSS / JavaScript のみ。ビルド・フレームワーク・パッケージ管理は使いません。
`architecture.md` で Phone は「未確定」のままであり、本 Issue の実装としてこの構成を選びました（設計書は変更していません）。

## 起動

### デモ（サーバ不要）

`betting.html` をブラウザで開き、URL の末尾に `?demo=1` を付けます。ファイルを直接開く形（`file://`）で動きます。

```
betting.html?demo=1
```

「次の場面」ボタンで、他の人の番 → 自分の番 → 所持1枚・在庫0あり → 第3レースのダブル指定 → 切断 → 仕込みへ進行、の順に切り替わります。
デモは架空データであり、実サーバとの接続やゲームルールの検証を代替しません。

### 実サーバへの接続

```
betting.html?server=http://127.0.0.1:8000&session=SESSION_ID&player=PLAYER_ID
```

`server` の既定は `http://127.0.0.1:8000` です。
設計上のルートは `/play/{sessionId}/betting` ですが、ロビー（Issue #24）が未実装で playerId を配る導線が無いため、
当面は URL パラメータで受けます。ロビー実装時に正規ルートへ寄せてください。
同期サーバとは別のオリジンから開く場合、サーバ側の CORS 許可が必要です。

## テスト

Node.js 21 以上が必要です（画面の表示自体に Node は不要）。

```sh
node --test "tests/hotstreak_phone/*.test.js"
```

状態ロジック・描画・通信エラー処理・起動配線（デモ操作を含む）を検証します。
描画テストは最小の DOM スタブ（`tests/hotstreak_phone/fake-dom.js`）で動かすもので、実機ブラウザでの表示確認の代わりにはなりません。

## 同期側との接続

- `GET /api/sessions/{sessionId}/betting` で初期状態・再接続時の状態を取得（API-BETTING-001）
- `WS /ws/sessions/{sessionId}` で `betting.state` / `betting.advanced` を購読
- 札の確定は `POST /api/sessions/{sessionId}/betting/picks`（API-BETTING-002）
- 第3レースのダブル指定は `PUT /api/sessions/{sessionId}/betting/double`（API-BETTING-003）
- `POST /api/sessions/{sessionId}/advance`（API-BETTING-004）は Display の操作なので送りません
- 購読を先に張ってから状態を取得し、その間のイベントを取りこぼさないようにしています
- 切断中は送信せず、再接続後に切断前の操作を遅れて送りません

設計のペイロードは概念定義で、WS 封筒のキー名は未指定です。
このクライアントでは次の形式を使用しています。**同期側 Issue #30 との結合時に照合が必要です。**

```json
{"type":"betting.state","payload":{
  "phase":"betting","raceIndex":1,"round":2,"turnIndex":3,"turnTotal":4,
  "currentPlayerId":"p1",
  "prompt":{"promptId":"sb-03","text":"コースアウトするマスコットはいる？"},
  "stock":[{"ticketId":"mascot-bear","ticketKind":"mascot","label":"くま","tier":"top","remaining":3}],
  "picksByPlayer":{"p1":[{"ticketInstanceId":"t-1","ticketId":"mascot-bear","ticketKind":"mascot","label":"くま","tier":"top","face":"risky"}]},
  "doubleByPlayer":{"p1":null},
  "players":[{"playerId":"p1","displayName":"ヤマダ"}]
}}
```

```json
{"type":"betting.advanced","payload":{"phase":"card-seed"}}
```

`ticketKind` は `mascot` / `side`、`tier` は `top` / `mid` / `bot`、`face` は `safe` / `risky` です。
`turnIndex` / `turnTotal` は手番バーの「何人目」の表示だけに使い、欠けていても動きます。

送信ボディも同様に未指定のため、次の形式で送ります（結合時に要照合）。
`api.md` の認証欄「手番 playerId」を満たす仕組みが未設計のため、`playerId` をボディに含めています。

```json
POST /betting/picks  {"playerId":"p1","ticketKind":"mascot","ticketId":"mascot-bear","face":"risky"}
PUT  /betting/double {"playerId":"p1","ticketInstanceId":"t-1"}
```

エラー文言は `features/betting/api.md` のエラー表に従います。
409 は複数の原因があるため、サーバが `{"message": "..."}` を返した場合はそれを優先します。

## 画面の決まり

- 山は Safe 面が上なので、札を選んだ直後は必ずセーフ。タップで裏返してリスキーにします
- 在庫0の札は無効表示にし、選択できません
- サイドベットのお題文面はスマホに表示しません（Display SCR-display-003 で会場に見せます）。
  ユーザー指示による調整で、`REQ-betting-003` のスマホ側表示を外しています。サーバは `prompt` を送る前提のままです
- サイド券（YES / NO）は横に2列で並べ、マスコット券は全幅で並べます
- 所持枠は常に2つ表示し、空き枠を見せます。投票ボタンと同じフッターに置き、スクロールしても見えるようにしています
- ダブル指定はレース3かつ所持2枚のときだけ表示します（レース1–2 では出しません）
- 手番・在庫・所持はサーバの値をそのまま表示し、スネーク順の計算をクライアントで再現しません
- 配当額は `features/payout/README.md` の観測確定表を `ticket-payouts.js` に持ちます
  （`api.md` に「payoutFaceValue は設計状態に含めない」とあるため、サーバからは受け取りません）
- `betting.advanced` を受けたら待機表示で止まります。次画面（SCR-phone-003）は Issue #36 の範囲です

## 検証と設計書の扱い

設計書は変更していません。
`features/betting/tests.md` は pytest（TST-betting-001〜004, 006, 007）と Playwright（TST-betting-005）を指定しますが、
前者は同期側 Issue #30 の範囲、後者は Display（Issue #31）と同期サーバが揃わないと成立しません。
本 Issue では追加依存なしの `node --test` で、状態ロジック・描画・通信エラー処理を検証しています。
実サーバ結合と E2E は結合時の検証事項です。
