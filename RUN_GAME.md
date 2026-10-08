# 実セッションの起動

既存の会場・スマホ画面を同期サーバに接続する入口です。固定モックの起動方法も従来どおり残しています。

## Windows

macOS / Linuxの通常起動は `./play.sh --windowed` です。Windowsと同じ `hotstreak_display.live` の会場UIと `hotstreak_sync.app` の実セッションを使用します。`--server` を指定する場合も、この実セッションサーバを指定してください。

Python 3.11以上で、初回だけリポジトリ直下から実行します。

```powershell
python -m venv .venv
.venv/Scripts/python -m pip install -r src/hotstreak_sync/requirements.txt -r src/hotstreak_display/requirements.txt
```

起動:

```powershell
powershell -ExecutionPolicy Bypass -File scripts/run-hotstreak.ps1 -Python .venv/Scripts/python.exe -Windowed
```

- 会場画面にQRを表示します。同じネットワーク上のスマホ1〜8台で参加してください。3人未満はCPUで補充します。
- QRのアドレスが違う場合は `-JoinOrigin http://会場PCのIPv4アドレス:8010` を指定します。
- 会場のEnterで公開カード準備 → マ券選び → カード仕込み → レースへ進みます。札選び・仕込みの未完了時には進めません。
- レース開始のGO後、Enter短押しで1枚、1秒長押しで自動進行を開始します。自動中はEnter押下で一時停止、1秒長押しで自動再開します。停止時も現在のカードの演出は最後まで表示します。長押しによる連続切替はしません。
- カード公開1.60秒と移動・短縮の演出が終わって0.5秒後に次を引きます。レース終了・通信エラー・フォーカス喪失でOFFになり、通信復帰後は1秒長押しで自動再開します。
- 結果画面のEnterで次レースのマ券選びへ。第3レース後はロビーに戻ります。
- 会場ウィンドウを閉じるとサーバも終了します。状態は設計どおりメモリ内のみで、サーバ終了時に失われます。
- Displayの再起動用認証情報は `.hotstreak-session.json` に保存します。Gitの対象外です。

## 会場のBGM・効果音

参加受付・準備・ベット・仕込み・配当では「いたずらスウィング」（40%）、レースではKevin MacLeod「Run Amok」（50%）を再生します。カード公開・移動・転倒・逆走・開始・ゴール・配当にも効果音が付きます。音声専用の操作は不要です。

音は会場端末からだけ出ます。音声デバイスや音源を利用できない場合はログに警告を出し、画面・Enter操作は続行します。OS側の音量も確認してください。

音源・ライセンス・実時間録画の再現手順: [assets/audio/README.md](assets/audio/README.md)。録画用のimageio-ffmpegはゲーム実行の必須依存ではありません。

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
- 再読込時は同じCookieの参加者として復帰します。`hotstreak_sync.app` の参加URLは `connection=session` を付け、`live.js` が接続します。既存の `hotstreak_sync.server` は `live-connection.js` を使用します。
- WS封筒は `{ "type": "race.state", "payload": {...} }`。再接続時は現在フェーズの全状態を受け取り、画面遷移も現在フェーズへ追従します。
- 同種の緑カードが複数あるため、`cardId` は種類、`cardInstanceId` は個体です。手札選択画面の選択用 `cardId` には個体IDを渡し、画像は `rect` を使用します。
- コースは2026-10-07ユーザー指定の13マス＋GOAL。STARTは3マス目、★は3・8・13マス目。内部座標は開始列2、★列2/7/12、ゴール境界13です。

コース座標に関する設計書だけをユーザー指定に合わせて更新しています。通信の重複排除・本人識別は未確定部分を具体化したもの、再読込時の復帰とDisplayの状態取得方式は既存設計との差分です。レビュー時にこの契約を確認してください。

## 検証

```powershell
python -m pip install pytest httpx
$env:PYTHONPATH='src'
$env:SDL_VIDEODRIVER='dummy'
$env:SDL_AUDIODRIVER='dummy'
python -m pytest tests/hotstreak_core tests/hotstreak_sync tests/hotstreak_display -q
node --test tests/hotstreak_phone/*.test.js
```

実ブラウザE2EはPlaywrightとEdgeを使います。Chromeの場合は `HOTSTREAK_BROWSER_CHANNEL=chrome` を指定できます。サーバ起動後:

```powershell
npm install --no-save playwright@1.62.1
$env:HOTSTREAK_TEST_URL='http://127.0.0.1:8010'
node tests/e2e/live-session.cjs
```

3つの独立ブラウザで、参加・名前入力・札選択・仕込み・3レース・個人配当・再参加を確認します。固定データの効果デモではなく、実サーバの抽選と精算を通します。

自動進行を含むE2Eは `HOTSTREAK_AUTO_RACE=1` を指定します（Python実行にuvが必要）。会場アプリの実HTTP接続とEnterイベントで、各レースの開始・演出中停止・再開・配当での停止を検証します。演出時計は高速化し、スマホは実ブラウザ3台で同期を確認します。ラズパイ実機の物理キー操作は別途確認してください。
