# Audio

音声素材を置く。

## サブフォルダ

| パス | 置くもの | 推奨形式 |
|------|----------|----------|
| `music/` | BGM（ループ想定） | OGG / MP3 |
| `sfx/` | 効果音（クリック、サイコロ、カードなど） | WAV / OGG |

## 置かないもの

- ボイス（必要になったら `voice/` を追加）
- 画像・フォント

## 命名例

- `music/bgm_title_loop.ogg`
- `sfx/sfx_dice_roll.ogg`
- `sfx/sfx_card_flip.wav`

## 参照例

`assets/audio/sfx/sfx_dice_roll.ogg`

## 会場BGM・効果音（audio / REQ-audio-001）

2026-10-08のユーザー選択: 待機はオリジナル③「いたずらスウィング」、レースはKevin MacLeod「Run Amok」、効果音はオリジナル8種類。
音付き試作の承認後、設計PR #116 → Epic #117 / 実装Issue #118 の正式フローで実装する。
正本: [会場BGM・効果音の設計](../../docs/design/hotstreak/features/audio/README.md)。

- `music/waiting.wav`: 参加受付・公開カード・ベット・仕込み・配当のBGM（40%）。
- `music/race.mp3`: レースBGM（50%）。原音は無加工で、再生時に音量を調整する。
- `sfx/se_*.wav`: 確定、カード公開、一歩、転倒、逆走、開始、ゴール、配当。
- `sfx/countdown_tick.wav` / `sfx/countdown_go.wav`: 開始音から切り出し、画面の3・2・1・GOに合わせて鳴らす。
- ライセンスと出典は `CREDITS.txt`。画面下にもレースBGMの帰属表示を出す。

会場Displayの `app.py` と `live.py` から使用する。一歩28%、その他の効果音68%。音声デバイスを開けない場合は警告を出してゲームを続行する。一部素材の欠落は該当音だけを省略する。
`live.py` ではカード集合・移動・最終カードの終了まで待ち、表示上の変化に効果音を合わせる。

録画の再現（実HTTP・実時間、参加者とEnter入力を自動操作）:

```sh
PYTHONPATH=src uv run --python 3.12 --with-requirements requirements.txt \
  --with imageio-ffmpeg python scripts/record-audio-preview.py --output /tmp/hotstreak-audio-preview
```

録画スクリプトは専用のローカルサーバと会場ウィンドウを開き、1レースを配当まで実行する。
描画フレームとSDLのミキサー出力を記録し、MP4・発音時刻ログ・確認画像を出力する。
音声を後からイベントに合わせて作り直す処理は行わない。
