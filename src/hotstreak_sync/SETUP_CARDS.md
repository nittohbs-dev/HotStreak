# 公開カード準備の同期（#26）

対象: `docs/design/hotstreak/features/setup-cards/`、REQ-setup-001〜007。
公開カードと手札の配布、状態取得、Enterによるbettingへの遷移を担当する。
画面・参加受付・マ券選択は別Issue。

## 接続

Python 3.11以上。`pip install -r src/hotstreak_sync/requirements.txt`。
`src` を `PYTHONPATH` に追加して利用する。

```python
from hotstreak_core.state import GameSession, Player
from hotstreak_sync.runtime import create_app

app = create_app()
runtime = app.state.runtime
# ロビー側が確定した参加者を登録。tokenは本人認証用で公開しない。
session = GameSession('session-id', [Player('a'), Player('b'), Player('c')])
runtime.add_session(session)
# ロビー完了ハンドラからawait（HTTPのdealエンドポイントは設けない）。
# await runtime.enter(session.session_id, 'setup-cards')
```

- GET `/api/sessions/{sid}/setup`: 公開カードと配布枚数。手札の内容は含めない。
- POST `/api/sessions/{sid}/advance`: JSON `{ "phase": "setup-cards", "revision": 1 }`。
  会場ループバックから `X-Display-Token` と `Idempotency-Key` を指定する。
  Displayは押下単位に操作IDを作り、再送時は同じID・本文を使う。
- WS `/ws/sessions/{sid}`: 接続時に現状を返し、配布・進行時に
  `setup.state` / `setup.advanced` を配信する。
- 別機能のサービスは `create_app([SetupCardsService(), ...])` に登録する。
  各サービスは `phase/section/event` と `enter/advance/snapshot` を持つ。
  後続betting側は遷移後に札ストック・ドラフト順を初期化する。

状態変更はセッションごとの排他区間で行い、失敗時は状態・乱数状態を復元する。
不一致revisionは409。成功済み同一操作の再送は保存済み結果を返す。
セッション・操作履歴はメモリのみ。単一プロセスで動かす（複数worker不可）。
操作履歴は直近1024件で、古い要求もrevisionにより再実行されない。
参加受付側が配布するCookie `hs_{sid}` のtokenで個人情報の閲覧者を決定する。

## 検証

`pip install pytest httpx` 後、`PYTHONPATH=src` で
`python -m pytest tests/hotstreak_core -q`。
3〜8人×30乱数でカード53個体の保存・重複なし、再入場、未配布進行拒否、
REST/WS、同時再送、認証、手札非公開を確認する。

## 設計書との対応

APIパスとイベント名は設計どおり。通信での二重実行を防ぐため、advanceに
revision・操作ID・Displayトークンを具体化した。供給データが不正な場合は
部分配布せず500とする（再抽選では破損した供給を修復できないため）。
永続化は設計どおり行わない。設計書・Display・Phoneファイルは変更しない。
