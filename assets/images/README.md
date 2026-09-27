# Images

画像素材を置く。推奨形式は PNG。

## サブフォルダ

| パス | 置くもの | 置かないもの |
|------|----------|--------------|
| `characters/` | 駒・立ち絵・スプライトシート | UI アイコン、盤面タイル |
| `board/` | 盤面・マス・タイル | カード絵柄、背景全体 |
| `cards/` | カード画像集（`cards_atlas.png`） | トークン、UI ボタン。個別 PNG を増やさない |
| `tokens/` | カウンター・マーカー・アイテム | キャラ駒、カード |
| `ui/` | ボタン・アイコン・HUD・カーソル | 背景、盤面 |
| `backgrounds/` | タイトル・対戦画面の背景 | 小さな UI パーツ |
| `effects/` | 演出フレーム・ヒット演出 | 常時表示の UI |

いま入っている実ファイルは次のとおりです。空の `board/` `tokens/` `ui/` `backgrounds/` `effects/` は置き場だけです。

| ファイル | 使い方 |
|----------|--------|
| `cards/cards_atlas.png` | Display `CardAssets` と Phone `card-sprite.js` が切り出すカード絵。再生成は [`cards/README.md`](cards/README.md) |
| `characters/card_mascots.png` | カード用の色別ドット（atlas 再生成の入力側） |
| `characters/card_mascots_source.png` | `tools/card-assets/build.py` の入力 |
| `characters/racers-approved.png` | レース／結果 Display の全身スプライト（4列×2段）。読み出しは `src/hotstreak_display/screens/race_sprites.py` |

## 命名例

- `characters/player_red_idle.png`
- `board/main.png`
- `cards/back.png`
- `ui/button_confirm.png`

## 参照例

`assets/images/board/main.png`
