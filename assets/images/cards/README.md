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

```python
from hotstreak_display.card_assets import CardAssets
assets = CardAssets()
surface.blit(assets.card("blue_swerve_1", (120, 168)), (0, 0))
surface.blit(assets.card("card_back", (100, 140)), (140, 0))
```

今後の画面もカードを独自描画せず、このローダーからIDで取り出してください。
画像の再生成は、依存パッケージと日本語フォントを用意して `python tools/card-assets/build.py`。
