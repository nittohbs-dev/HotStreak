# 公開カード画面（Issue #27）

SCR-display-002 / REQ-setup-002・003（受信表示）、005・006（Display側）。
Pygameで公開カードを表示し、配布完了後のEnterを同期サーバへ送ります。
抽選・手札配布・同期サーバ・ロビー・マ券画面は含みません。

## 起動

Python 3.11以上で、リポジトリのルートから実行します。依存は `pygame==2.6.1` と `websocket-client==1.8.0` です。

```sh
python -m pip install -r src/hotstreak_display/requirements.txt
python src/hotstreak_display/screens/setup_cards.py --demo --windowed
python src/hotstreak_display/screens/setup_cards.py --session SESSION_ID --server http://127.0.0.1:8000
```

| フラグ | 内容 |
|--------|------|
| `--demo` | 架空データで描画。サーバに接続しない |
| `--session` | 実接続時のセッションID。`--demo` が無いとき必須。URL エンコードする |
| `--server` | `http(s)://host[:port][/path]`。既定 `http://127.0.0.1:8000`。query / fragment は不可 |
| `--players` | デモ人数 3〜8。既定 4。公開枚数は `18 - 人数` |
| `--font` | 日本語 TTF/OTF。未指定時は游ゴシック・メイリオ・Noto Sans CJK・IPAゴシックを探索 |
| `--windowed` | 1280×720 論理画面をウィンドウ表示（リサイズ可・レターボックス） |
| `--screenshot PATH` | デモを PNG 保存して終了。`--demo` 必須 |

既定は全画面。Esc またはウィンドウ閉じで終了。フォントや画像素材は同梱していません。
デモは架空データであり、実サーバとの接続やゲームルールの検証を代替しません。

```sh
python src/hotstreak_display/screens/setup_cards.py --demo --players 3 --screenshot setup_cards.png
python -m unittest discover -s tests/hotstreak_display -v
```

テストは `SDL_VIDEODRIVER=dummy` を使います。描画テストは日本語フォントが無いとスキップします。

## 同期側との接続

- `GET /api/sessions/{sessionId}/setup` で初期状態・再接続時の状態を取得。
- `WS /ws/sessions/{sessionId}` で `setup.state` / `setup.advanced` を購読。
- 配布完了時のみ `POST /api/sessions/{sessionId}/advance` を送信。
- `phase=betting` のサーバ応答・通知で `on_advanced("betting")` を一度だけ呼びます。
  単独ランナーはここで終了します。統合時は画面管理側のコールバックに次画面切替を接続します。
- 切断時は進行操作を止め、再接続を試みます。Enter押下だけで楽観的に次へ進めません。
- ネットワーク待機は別スレッドで処理し、Pygame操作はメインスレッドに限定しています。

設計のペイロードは概念定義で、WS封筒のキー名は未指定です。
この接続アダプタでは次の形式を使用しています。同期側Issue #26との結合時に照合が必要です。

```json
{"type":"setup.state","payload":{"phase":"setup-cards","playerCount":8,"dealt":false,"faceUpCards":[]}}
```

配布完了時の `faceUpCards` は `cardId`, `mascot`, `effectLabel`, `lane` を持ちます。
`dealt=true` のとき枚数は `18 - playerCount`（3人なら15、8人なら10）。未配布でも最大15枚、`cardId` 重複は拒否します。
`playerCount` は 3〜8 の整数。`phase` を省略すると `setup-cards` とみなし、それ以外は拒否します。
公開枚数はサーバの値を表示し、クライアントでカードを抽選・補完しません。
`hands` など非公開手札は読み捨て、表示状態に取り込みません。
11枚以上はコンパクトグリッド（5列）で描画します。

`GET` / `POST` の HTTP エラーは次の文言にします。409 は GET と POST で意味が違います。

| 状態 | GET `/setup` | POST `/advance` |
|------|----------------|-----------------|
| 404 | セッションが見つかりません | 同左 |
| 409 | 公開カードのフェーズではありません | 準備中、またはこの操作はできません |
| 500 | カードの準備に失敗しました。セッションを再作成してください。 | 同左 |

切断時は未送信の Enter を捨て、再接続後に遅れ実行しません。
`POST /advance` のボディは `{}` です。`phase=betting` 以外の成功応答はエラー扱いにします。

## 検証と設計書の扱い

設計書は変更していません。ユーザー指示によりPygameで実装し、
テスト章のPlaywright指定に対してPythonテスト・Pygame描画検証を使用します。
実サーバ未実装のため、完全なゲーム進行E2Eは結合時の検証事項です。

## よくあるつまずき

| 症状 | 確認すること |
|------|----------------|
| `日本語フォントが必要です` | OS に対象フォントが無いか。`--font` で TTF/OTF を渡す |
| `--session または --demo が必要です` | どちらか一方を付ける |
| `--screenshot は --demo と併用` | スクリーンショットはデモ専用 |
| `server は http(s)://…` | スキームは http/https。query / fragment は付けない |
| Enter しても進まない | `dealt=true`・接続中・未 pending であること。切断中は送れない |
| 公開カードを確認できません | 人数・枚数・重複・`phase` が上の制約を満たしているか |
