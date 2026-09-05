# Assets

Pygame 向けゲーム素材のルートディレクトリ。

## 構成

| パス | 用途 |
|------|------|
| `images/` | 画像（キャラ、盤、カード、UI など） |
| `audio/` | 音声（BGM・効果音） |
| `fonts/` | フォント |

## 命名規則

- `snake_case` を使う
- 用途が分かる名前にする

例:

- `player_red_idle.png`
- `sfx_dice_roll.ogg`
- `bgm_title_loop.ogg`

## 推奨フォーマット

| 種類 | 形式 |
|------|------|
| 画像 | PNG |
| BGM | OGG / MP3 |
| 効果音 | WAV / OGG |
| フォント | TTF / OTF |

## Pygame からの参照例

```python
from pathlib import Path

ASSETS = Path(__file__).resolve().parent.parent / "assets"
board_image = ASSETS / "images" / "board" / "main.png"
```

## 置かないもの

- カード定義 JSON などのゲームデータ（`data/` や `src/` 側へ）
- 動画（現状不要）
