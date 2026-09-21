# HotStreak

予測不能なドタバタ劇！ボードゲーム『ホットストリーク』を作ってみよう。

## ドキュメント

| パス | 内容 |
|------|------|
| [`docs/design/hotstreak/`](docs/design/hotstreak/) | ゲーム本体の設計書（骨格） |
| [`docs/design/hotstreak/manual.html`](docs/design/hotstreak/manual.html) | デジタル版の説明書（草案・ブラウザ閲覧） |
| [`docs/design/wireframes/`](docs/design/wireframes/) | 画面ワイヤー・ラフ（phone / display） |
| [`docs/design/wireframes/phone/DESIGN.md`](docs/design/wireframes/phone/DESIGN.md) | スマホ UI ビジュアル基準 |
| [`docs/design/wireframes/display/DESIGN.md`](docs/design/wireframes/display/DESIGN.md) | ディスプレイ UI ビジュアル基準 |
| [`docs/design/spec-browser/`](docs/design/spec-browser/) | 設計把握ビューアの設計書 |
| [`AGENTS.md`](AGENTS.md) | エージェント向け前提 |

開発フロー・ブランチ規則は [`.agents/AGENTS.md`](.agents/AGENTS.md) を参照。実装中の `docs/design/` はリードオンリーです。

## 開発者向け

いま動かせる実装は次のとおりです。セットアップとつまずきは各 README にあります。

| もの | 前提 | 入口 |
|------|------|------|
| 設計把握ビューア | Node.js（Pages ビルドは 22） | [`tools/spec-browser/README.md`](tools/spec-browser/README.md) |
| 公開カード Display | Python 3.11+、日本語フォント | [`src/hotstreak_display/README.md`](src/hotstreak_display/README.md) |
| マ券ドラフト Display（モック） | 同上 | [`src/hotstreak_display/BETTING_MOCK.md`](src/hotstreak_display/BETTING_MOCK.md) |
| カード仕込み Display（モック） | 同上 | [`src/hotstreak_display/CARD_SEED_MOCK.md`](src/hotstreak_display/CARD_SEED_MOCK.md) |
| マ券ドラフト Phone | ブラウザ（テストは Node.js 21+） | [`src/hotstreak_phone/README.md`](src/hotstreak_phone/README.md) |
| 共通カード画像 | Display と同じ依存 | [`assets/images/cards/README.md`](assets/images/cards/README.md) |

```bash
# 設計キャンバス（docs/design の索引を自動生成）
cd tools/spec-browser && npm install && npm run dev

# 公開カード画面のデモ（ルートから）
python -m pip install -r src/hotstreak_display/requirements.txt
python src/hotstreak_display/screens/setup_cards.py --demo --windowed

# マ券ドラフトのスマホ画面デモ
# ブラウザで src/hotstreak_phone/betting.html?demo=1 を開く
```

同期サーバ・ロビー・レース進行・配当精算は未実装です。Display / Phone のデモは架空データで描画だけ確認します。カード絵は `CardAssets` が `data/cards/catalog.json` から切り出します。素材の置き場は [`assets/README.md`](assets/README.md) です。
