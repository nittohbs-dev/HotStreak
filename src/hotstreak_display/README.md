# 公開カード画面（Issue #27）

SCR-display-002 / REQ-setup-002・003（受信表示）、005・006（Display側）。
Pygameで公開カードを表示し、配布完了後のEnterを同期サーバへ送ります。
抽選・手札配布・同期サーバ・ロビー・マ券画面は含みません。

## 起動

Python 3.11以上で、リポジトリのルートから実行します。

```sh
python -m pip install -r src/hotstreak_display/requirements.txt
python src/hotstreak_display/screens/setup_cards.py --demo --windowed
python src/hotstreak_display/screens/setup_cards.py --session SESSION_ID --server http://127.0.0.1:8000
```

既定は全画面。Escで終了。日本語フォントはOSの游ゴシック・メイリオ・Noto Sans CJK・IPAゴシックから探索します。
見つからない場合は `--font /path/to/japanese.ttf` を指定してください。フォントや画像素材は同梱していません。
デモは架空データであり、実サーバとの接続やゲームルールの検証を代替しません。
`--players 3`〜`--players 8`で枚数を確認できます。

```sh
python src/hotstreak_display/screens/setup_cards.py --demo --players 3 --screenshot setup_cards.png
python -m unittest discover -s tests/hotstreak_display -v
```

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

配布完了時の `faceUpCards` は `cardId`, `mascot`, `effectLabel`, `lane` を持つ10〜15枚です。
公開枚数はサーバの値を表示し、クライアントでカードを抽選・補完しません。
手札の中身は表示状態に取り込みません。

## 検証と設計書の扱い

設計書は変更していません。ユーザー指示によりPygameで実装し、
テスト章のPlaywright指定に対してPythonテスト・Pygame描画検証を使用します。
実サーバ未実装のため、完全なゲーム進行E2Eは結合時の検証事項です。
