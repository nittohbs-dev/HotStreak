# レース進行の同期（#44）

対象: `docs/design/hotstreak/features/race/`、REQ-race-001〜007。
前提: #26 の共通状態・カード供給・同期runtime。これを先に合併する。
Pythonのnamespace packageとして同じ `src` 配下に組み合わさる。

```python
from hotstreak_core.setup_cards import SetupCardsService
from hotstreak_core.race_service import RaceService
from hotstreak_sync.runtime import create_app
app = create_app([SetupCardsService(), RaceService()])
```

仕込み側は各Playerの `seed` を手札から取り除き、`public_cards` と合わせて
異なる18個体を用意する。`prompts` にカタログのeventカード一覧と
`prompt_index` を設定し、`await runtime.enter(sid, 'race')` で開始する。
バーン3枚後、Enter待ち。キーリピート抑止はDisplayの責務。

GET `/api/sessions/{sid}/race` と WS `/ws/sessions/{sid}` で状態を取得する。
Enterは既存POST `advance` を使用し、phase= `race`、revision、操作IDを送る。
認証・再送仕様はSETUP_CARDS.mdと共通。1操作1枚、サーバ上で効果・順位を確定。
終了時は `race.finished` に `standings/sideBetOutcome/phase=payout` が入り、
配当サービス登録済みなら同じ排他区間で精算し `payout.state` も送る。
配当サービス未登録でも確定結果は保持する。手札・未公開の山・バーン札は配信しない。
`myBets` は本人Cookieで取得。queryのplayerId指定では本人を切り替えない。

全カード効果・3列短縮・再シャッフル/再バーン・下位からのDQ順位・同時DQの
同率下位配当・3体終了時の残り順位・12種サイドベット成否を計算する。
状態の `beforeShortening/events` は画面が効果と崩壊を順に演出するための情報。

## 検証

#26合併後、`PYTHONPATH=src` で `python -m pytest tests/hotstreak_core -q`。
合併前は #26と本ブランチのsrcを両方PYTHONPATHに指定する。
純粋な効果テストとREST/WSのバーン→めくり→終了、再送、本人認証を検証。
画面接続・演出E2Eは本PRの対象外。

## 設計書との差分

- Enter通信契約のOPENを、既存advance + revision + 操作IDとして実装した。
- ユーザー確認済みモックに合わせ、START=2、星=0/5/8/12、GOAL=12。
  REQ-race-007の旧座標（星3/6/9）とは異なる。4レーン×12マスは維持。
- myBetsのplayerIdはCookie認証から決定し、他人のなりすましを防ぐ。

設計ファイルは変更せず、上記をPRの確認点とする。
