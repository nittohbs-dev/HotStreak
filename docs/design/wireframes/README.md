# ワイヤーフレーム・画面設計（ラフ）

見た目の正本は HTML / PNG。ルール・流れ・用語の正本は [`../hotstreak/00-project/overview.md`](../hotstreak/00-project/overview.md)。

| パス | 内容 |
|------|------|
| [phone/DESIGN.md](./phone/DESIGN.md) | スマホ画面設計（横断・SCR-phone-*） |
| [display/DESIGN.md](./display/DESIGN.md) | ディスプレイ画面設計（横断・SCR-display-*） |
| [phone/](./phone/) | スマホ側ラフ（HTML） |
| [display/](./display/) | ディスプレイ側ラフ（PNG） |

機能別の REQ / API 正本は `hotstreak/features/<機能ID>/screens.md`。横断 `DESIGN.md` は `tools/design/build_wireframe_design_md.py` で再生成する。

## 正規フローと二画面対応

| フェーズ | ディスプレイ | スマホ |
|----------|--------------|--------|
| 参加・ロビー | QR、参加者一覧 | スキャン、名前入力。次へは全員揃いまたは Enter |
| 公開カード準備 | 表向きカードの一覧 | （参照・待ち）。Enter／揃いでマ券へ |
| マ券・サイドベット | お題・在庫の共有表示 | スネークドラフト。全員2枚または Enter |
| カード仕込み | （待ち／束の準備表示） | 手札1枚。全員済または Enter（時間制限なし） |
| レース進行 | バーン、めくり、移動、コース短縮、着順 | 観戦（自分のマ券・金額・順位）。全員状況はボタン→小画面 |
| 配当 | 着順・お題結果 | 個人の払戻・所持金。次へは Enter |
| レース間 | コース／マスコットリセット、新お題 | Enter 後に手札補充反映 |

## 旧ワイヤー注記

- [phone/hotstreak-wireframes.html](./phone/hotstreak-wireframes.html) は画面レイアウトの参考。遷移順（提出→馬券）や時間遷移（20秒／15秒）は**採用しない**
- [display/試合開始前設計.png](./display/試合開始前設計.png) は開始前後のビジュアル参考。順序の定義は overview の正規フロー
- [display/ゲーム進行画面-ディスプレイ側.png](./display/ゲーム進行画面-ディスプレイ側.png) の「コース崩壊」はルール上の**コース短縮**として読む

横断画面設計は `phone/DESIGN.md` と `display/DESIGN.md`。仕様の正本は `hotstreak/features/<id>/screens.md`（spec-browser・Issue が参照）。
