# スマホ画面

| 画面 | ファイル | Issue | 内容 |
|------|----------|-------|------|
| SCR-phone-001 ロビー（参加） | `lobby.html` | #24 | 参加・名前確定・参加者一覧 |
| SCR-phone-002 マ券ドラフト | `betting.html` | #32 | 札の取得・セーフ／リスキー・第3ダブル |

同期サーバ・Display 画面・カード仕込み以降の画面は含みません。

## 技術

素の HTML / CSS / JavaScript のみ。ビルド・フレームワーク・パッケージ管理は使いません。
`architecture.md` で Phone は「未確定」のままであり、実装としてこの構成を選びました（設計書は変更していません）。

共通の色・レイアウトは `phone.css` に置き、画面固有の指定だけ `lobby.css` / `betting.css` に分けています。
各画面は「状態（`*-state.js`）・通信（`*-connection.js`）・描画（`*-view.js`）」の三分割で、状態はブラウザ無しでテストできます。

## テスト

Node.js 21 以上が必要です（画面の表示自体に Node は不要）。

```sh
node --test "tests/hotstreak_phone/*.test.js"
```

状態ロジック・描画・通信エラー処理・起動配線（デモ操作を含む）を検証します。
描画テストは最小の DOM スタブ（`tests/hotstreak_phone/fake-dom.js`）で動かすもので、実機ブラウザでの表示確認の代わりにはなりません。

## 検証と設計書の扱い

設計書は変更していません。
各機能の `tests.md` は pytest と Playwright を指定していますが、pytest 対象は同期側（Issue #22 / #30）の範囲、
Playwright の E2E は Display と同期サーバが揃わないと成立しないため、追加依存なしの `node --test` で代替しています。
実サーバ結合と E2E は結合時の検証事項です。

---

# ロビー画面（Issue #24）

SCR-phone-001 / REQ-lobby-002〜006（スマホ側）。QR から参加し、名前を確定して参加者一覧を同期します。

## 起動

```
lobby.html?demo=1                                    # サーバ不要のデモ
lobby.html?server=http://127.0.0.1:8000&session=SESSION_ID
```

デモは「参加直後 → ほかの人が入力 → 全員そろった → 公開カードの準備中 → マ券ドラフトへ」を順に切り替えます。

設計上のルートは `/join/{sessionId}` ですが、静的配信のため当面 `session` を URL パラメータで受けます。
QR の生成・表示は Display（Issue #23）の担当です。

## 同期側との接続（Issue #22 と要照合）

- 購読を張ってから `POST /api/sessions/{sessionId}/join`（API-LOBBY-003）で `playerId` を得ます
- 名前確定は `PUT /api/sessions/{sessionId}/players/{playerId}/name`（API-LOBBY-004）、ボディは `{"displayName":"ヤマダ"}`
- `WS /ws/sessions/{sessionId}` で `lobby.state` / `lobby.advanced` / `setup.advanced` を購読します
- `POST /api/sessions`（API-LOBBY-001）と advance（API-LOBBY-005）は Display の操作なので送りません
- 再接続時は join し直さず `GET /api/sessions/{sessionId}` で状態を取り直します（再参加はスコープ外のため）

```json
{"type":"lobby.state","payload":{
  "sessionId":"sess_1","phase":"lobby",
  "players":[{"playerId":"p_1","displayName":"ヤマダ","nameReady":true,"balance":10}]
}}
```

```json
{"type":"lobby.advanced","payload":{"phase":"setup-cards"}}
```

公開カード中は Phone 専用画面が無いため待機表示にし、`setup.advanced`（`{"phase":"betting"}`、Issue #27 が定義した封筒）を
受けたらマ券画面へ `session` と `player` を引き渡して遷移します。

エラー文言は `features/lobby/api.md` のエラー表に従います。
join の 409 は「満員」と「受付終了」の2種類があるため、サーバが `{"message": "..."}` を返した場合はそれを優先します。

## 画面の決まり

- 空の名前では確定ボタンを押せません（前後の空白は取り除いて送ります）
- 名前変更 API は設計に無いため、確定後は入力欄とボタンを閉じます
- 未入力の人は名前を伏せて「入力中」と出します
- 進行の判定（全員そろい）は 3 人以上そろってからです（BR-lobby-007）
- 名前未入力のまま Enter で進んだ場合、`プレイヤーN` を付けるのはサーバの担当です（BR-lobby-005 / REQ-lobby-007）。
  スマホは付いた名前を受け取る手段が封筒に無いため表示しません（会場の Display で確認する前提）。
  進行後に届いた `lobby.state` は phase が `lobby` でなくなるため取り込みません
- 所持金はサーバから受け取っても画面には出しません（ワイヤーに無いため）

---

# マ券ドラフト画面（Issue #32）

SCR-phone-002 / REQ-betting-001〜006（スマホ側）。
スネークドラフトで札を1枚選び、セーフ／リスキーを決めて確定します。第3レースのみ所持2枚から1枚をダブル指定します。

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
通常はロビー画面（`lobby.html`）が `session` と `player` を引き渡して遷移するため、手で URL を組む必要はありません。
設計上のルートは `/play/{sessionId}/betting` ですが、静的配信のため当面は URL パラメータで受けます。
同期サーバとは別のオリジンから開く場合、サーバ側の CORS 許可が必要です。

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
