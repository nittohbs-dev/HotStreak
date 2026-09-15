# スマホ側ワイヤー（ラフ）

| ファイル | 内容 |
|----------|------|
| [DESIGN.md](./DESIGN.md) | 画面設計（横断・SCR-phone-*・正規フロー寄せ） |
| [hotstreak-wireframes.html](./hotstreak-wireframes.html) | 見た目ラフ一覧（ブラウザで開く） |
| [screen-01-title.html](./screen-01-title.html) | タイトル画面単体ラフ |

## 画面一覧（HTML上のラベル → 設計上の対応）

| HTMLラベル | 設計上のフェーズ | 備考 |
|------------|------------------|------|
| 1. タイトル | lobby | QR・名前。次へは全員揃いまたはラズパイ Enter |
| 2. カード提出 | card-seed | **仕込み**に相当。HTMLの「提出→馬券」順は旧。正規はマ券のあと |
| 3. 馬券選択 | betting | 表記は**マ券**。ノーマル→**セーフ**。全体×2→**1枚ダブル** |
| 4. レース中 | race | 下部は自分のマ券・金額・順位。「全員の状況」で小画面 |
| 4b. 全員状況 | race（モーダル） | 他プレイヤーのマ券一覧 |
| 5. 結果発表 | payout | 配当・所持金 |

画面の横断ビューは [DESIGN.md](./DESIGN.md)。REQ 正本は `hotstreak/features/*/screens.md`。ルールは [`../../hotstreak/00-project/overview.md`](../../hotstreak/00-project/overview.md)。
