# 実セッションの起動

既存の会場・スマホ画面を同期サーバに接続する入口です。固定モックの起動方法も従来どおり残しています。

## Windows

Python 3.11以上で、初回だけリポジトリ直下から実行します。

```powershell
python -m venv .venv
.venv/Scripts/python -m pip install -r src/hotstreak_sync/requirements.txt -r src/hotstreak_display/requirements.txt
```

起動:

```powershell
powershell -ExecutionPolicy Bypass -File scripts/run-hotstreak.ps1 -Python .venv/Scripts/python.exe -Windowed
```

- 会場画面にQRを表示します。同じネットワーク上のスマホ3〜8台で参加してください。
- QRのアドレスが違う場合は `-JoinOrigin http://会場PCのIPv4アドレス:8010` を指定します。
- 会場のEnterで公開カード準備 → マ券選び → カード仕込み → レースへ進みます。札選び・仕込みの未完了時には進めません。
- レース中はEnter 1押下につき1枚。押しっぱなし・演出中の追加入力は受け付けません。
- 結果画面のEnterで次レースのマ券選びへ。第3レース後はロビーに戻ります。
- 会場ウィンドウを閉じるとサーバも終了します。状態は設計どおりメモリ内のみで、サーバ終了時に失われます。
- Displayの再起動用認証情報は `.hotstreak-session.json` に保存します。Gitの対象外です。

## サーバとDisplayを別々に起動する場合

両ターミナルで `$env:PYTHONPATH='src'` を設定し、次を実行します。

```powershell
python -m uvicorn hotstreak_sync.app:app --host 0.0.0.0 --port 8010
python -m hotstreak_display.live --server http://127.0.0.1:8010 --join-origin http://会場PCのIPv4アドレス:8010 --windowed
```

サーバは**1ワーカー**で動かします。スマホのURLは `/join/{sessionId}`。独立した参加者としてPCだけで確認する場合は、Cookieが独立したブラウザプロファイルを使ってください。

## 実装範囲

- 公開カード準備: 53枚の物理個体を区別し、各色の `recover_2` をスターターとして配布。公開枚数は `18 − 参加人数`、手札は各3枚。
- レース: 個別移動・逆走・★・転倒・復帰・スワーブ・衝突・全員カード、3枚バーン、山切れ時3列短縮、ゴールとDQの着順、12種のサイドベット事実。
- 配当: 札のtier/表裏、選択した1枚のダブル、残高下限0、二重精算防止、既存レース山からの手札補充、先頭ローテーション、共同優勝。
- 上記を実データでつなぐため、参加・スネークドラフト・手札仕込みの入口も実装しています。
- coreはpygame/FastAPIに依存しません。Displayはサーバ座標間を補間し、金額や効果の判定は行いません。PhoneはWebSocket購読、Displayは状態取得とEnter送信を行います。

## 接続契約の具体化

既存APIのパスを使用しています。レースのEnter要求は既存 `POST /api/sessions/{id}/advance` に統一しました。

- 作成応答の `displayToken` を会場側だけで保持し、Enterには `X-Display-Token` を付けます。作成・進行はループバック接続限定です。
- 更新要求には `Idempotency-Key` が必要です。Enterの本文は `{ "phase": "race", "revision": 12 }` のように画面で確認した状態を指定します。同じ操作IDの再送は同じ応答、古いrevisionの別操作は409です。
- 参加応答でHttpOnly / SameSite Cookieを設定し、手札・仕込み札・個人配当は本人だけへ返します。公開playerIdを指定するだけでは他人の手札を取得できません。
- 再読込時は同じCookieの参加者として復帰します。古い通信実装は固定モック検証用に残し、実セッション指定時は `live.js` が接続を担当します。
- WS封筒は `{ "type": "race.state", "payload": {...} }`。再接続時は現在フェーズの全状態を受け取り、画面遷移も現在フェーズへ追従します。
- 同種の緑カードが複数あるため、`cardId` は種類、`cardInstanceId` は個体です。手札選択画面の選択用 `cardId` には個体IDを渡し、画像は `rect` を使用します。
- コースはユーザー確認済みのゲーム画面に合わせて、開始列2、★列0/5/8/12、ゴール12を使用しています。設計書に残る旧座標とは異なります。

設計書自体は編集していません。通信の重複排除・本人識別は未確定部分を具体化したもの、再読込時の復帰とDisplayの状態取得方式は既存設計との差分です。レビュー時にこの契約を確認してください。

## 検証

```powershell
python -m pip install pytest httpx
$env:PYTHONPATH='src'
$env:SDL_VIDEODRIVER='dummy'
$env:SDL_AUDIODRIVER='dummy'
python -m pytest tests/hotstreak_core tests/hotstreak_sync tests/hotstreak_display -q
node --test tests/hotstreak_phone/*.test.js
```

実ブラウザE2EはPlaywrightとEdgeを使います。サーバ起動後:

```powershell
npm install --no-save playwright@1.62.1
$env:HOTSTREAK_TEST_URL='http://127.0.0.1:8010'
node tests/e2e/live-session.cjs
```

3つの独立ブラウザで、参加・名前入力・札選択・仕込み・3レース・個人配当・再参加を確認します。固定データの効果デモではなく、実サーバの抽選と精算を通します。
