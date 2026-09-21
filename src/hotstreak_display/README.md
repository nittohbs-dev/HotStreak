# 会場ディスプレイ（Pygame）

会場向け画面は 1280×720 論理解像度です。共通の部屋背景・日本語書体・カード絵は `DisplaySetupRoot` と `CardAssets` が持ちます。

| 画面 | 対象 | 通信 | 起動 |
|------|------|------|------|
| 公開カード | SCR-display-002 / Issue #27 | あり（`--demo` 以外） | `screens/setup_cards.py` |
| マ券ドラフト | SCR-display-003 / Issue #31 | なし（固定見本） | [`BETTING_MOCK.md`](BETTING_MOCK.md) |
| カード仕込み | SCR-display-004 / Issue #35 | なし（固定見本） | [`CARD_SEED_MOCK.md`](CARD_SEED_MOCK.md) |

抽選・手札配布・同期サーバ本体・ロビー・レース画面は含みません。カード絵は同梱の画像集から ID で切り出します。手順は [`assets/images/cards/README.md`](../../assets/images/cards/README.md)。

## 共通の起動前提

Python 3.11以上で、リポジトリのルートから実行します。依存は `pygame==2.6.1` と `websocket-client==1.8.0` です。

```sh
python -m pip install -r src/hotstreak_display/requirements.txt
```

日本語フォントは游ゴシック・メイリオ・Noto Sans CJK・IPAゴシックから探索します。無い場合は `--font /path/to/japanese.ttf` を指定してください。フォント本体は同梱していません。

既定は全画面。`--windowed` で 1280×720 論理画面をウィンドウ表示し、リサイズ時はレターボックスします。

```sh
python -m unittest discover -s tests/hotstreak_display -v
```

テストは `SDL_VIDEODRIVER=dummy` を使います。描画テストは日本語フォントが無いとスキップします。

---

# 公開カード画面（Issue #27）

SCR-display-002 / REQ-setup-002・003（受信表示）、005・006（Display側）。
Pygameで公開カードを表示し、配布完了後のEnterを同期サーバへ送ります。

## 起動

```sh
python src/hotstreak_display/screens/setup_cards.py --demo --windowed
python src/hotstreak_display/screens/setup_cards.py --session SESSION_ID --server http://127.0.0.1:8000
```

| フラグ | 内容 |
|--------|------|
| `--demo` | カタログ上の架空並びで描画。サーバに接続しない |
| `--session` | 実接続時のセッションID。`--demo` が無いとき必須。URL エンコードする |
| `--server` | `http(s)://host[:port][/path]`。既定 `http://127.0.0.1:8000`。query / fragment は不可 |
| `--players` | デモ人数 3〜8。既定 4。公開枚数は `18 - 人数` |
| `--font` | 日本語 TTF/OTF |
| `--windowed` | ウィンドウ表示 |
| `--screenshot PATH` | デモを PNG 保存して終了。`--demo` 必須 |

Esc またはウィンドウ閉じで終了。デモは描画確認用であり、実サーバとの接続やゲームルールの検証を代替しません。

```sh
python src/hotstreak_display/screens/setup_cards.py --demo --players 3 --screenshot setup_cards.png
```

デモの `cardId` はカタログの `blue_move_2` などです。カタログに無い ID は裏面を出し、`effectLabel` を重ねます。

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
10枚以下は5列、11枚以上は8列で描画します。

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
| カードが裏面だけ | `cardId` が `data/cards/catalog.json` にあるか |
