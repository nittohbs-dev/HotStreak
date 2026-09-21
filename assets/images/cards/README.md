# 共通カード画像集

`cards_atlas.png` に、レーサー44種・緑6種・黒いイベント12種・共通裏面1種の計63画像を収録。
重複枚数を含めると実物の表面は65枚。裏面は写真がないためモック用のオリジナルです。

- `data/cards/catalog.json`: 各カードID、種類、色、表示文言、枚数、切り出し位置。
- `src/hotstreak_display/card_assets.py`: 共通読み込み・サイズ別キャッシュ。
- `assets/images/characters/card_mascots.png`: 色別ドットキャラクター画像集。
- `tools/card-assets/build.py`: 画像集・カタログを再生成するスクリプト。

ユーザー提供のカード写真6枚と `hot streak cards.md` を参考に作成。
キャラクター絵は写真をもとに画像生成でデフォルメし、文字・数値・カード枠はコードで配置しています。
写真そのもの・PCや周辺の写り込みはリポジトリへ入れていません。
色IDは維持し、表示名は青＝ダングル、オレンジ＝ゴブラー、黄＝マム、サーモン＝ハーレーです（ユーザー指定）。
黒はイベントのお題（サイドベット）。固有名入りの4枚も同じ日本語名を表示します。
星カードは星の表示のみで効果は推測していません。

## 使用

画面スクリプトと同じく、`src/hotstreak_display` をパスに入れてから読みます。

```python
from card_assets import CardAssets
assets = CardAssets()
surface.blit(assets.card("blue_swerve_1", (120, 168)), (0, 0))
surface.blit(assets.card("card_back", (100, 140)), (140, 0))
icon = assets.icon("青", (48, 48))  # "blue" でも可
```

| メソッド | 内容 |
|----------|------|
| `card(card_id, size)` | atlas から切り出し、指定サイズへ平滑拡大してキャッシュ |
| `icon(color, size)` | `blue` / `orange` / `salmon` / `yellow`、または日本語色名。緑・黒は無し（`None`） |
| `race_cards()` | `kind == "race"` のカタログ行 |

ID 規則: レーサーは `{color}_{effect}`（例 `blue_swerve_1`）、緑は `green_move_2`、イベントは `event_{key}`（例 `event_disqualified`）、裏面は `card_back`。未知の ID は `KeyError` です。画面側で無い ID を裏面に落とす処理は各画面の責務です。

今後の画面もカードを独自描画せず、このローダーからIDで取り出してください。

## 再生成

```sh
python -m pip install -r src/hotstreak_display/requirements.txt
python tools/card-assets/build.py
```

- ルートから実行する。`SDL_VIDEODRIVER=dummy` をスクリプト側で設定する。
- 日本語フォントが必要。無いと `日本語フォントが必要です` で止まる。
- 入力は `assets/images/characters/card_mascots_source.png`。出力は `cards_atlas.png`・`card_mascots.png`・`data/cards/catalog.json`。
- ゲーム効果の処理は含めない。星カードは星の表示のみ。
- 枚数の期待値はテストどおり 63 画像 / 実物表面 65 枚（緑の重複枚を含む）。

