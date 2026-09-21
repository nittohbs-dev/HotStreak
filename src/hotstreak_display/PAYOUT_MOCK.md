# payout ディスプレイモック（Issue #42）

既存の背景・金色の枠とゲーム中と同じ採用済み全身キャラクター素材を利用する1280×720の固定表示例です。
設計書は変更しません。通信・ゲーム演算・画面間の接続は未実装です。
このモックだけでIssue全体の受け入れ条件を満たすものではありません。

```sh
python -m pip install -r src/hotstreak_display/requirements.txt
python src/hotstreak_display/screens/payout.py --windowed
```

- `--state`: normal / dq / tie
- `--screenshot path.png`: 画面をPNG保存して終了。
- `--font path.ttf`: 日本語フォント指定。既定はOSの日本語フォント。
- 全画面が既定。ウィンドウの閉じる操作で終了。Esc・矢印キーによる遷移はありません。
- 表示は時間経過で進みません。各状態は起動引数で選びます。

`--race 1`〜`3`。Enterで進行確認を表示し、1・2レース後はマ券選び、3レース後はロビーの案内を出します。`--state tie`は最終レースの共同優勝例です。金額計算は行いません。

表彰台と4位・失格欄は `race_sprites.py` と `assets/images/characters/racers-approved.png` を使用。FINISHと「次のレースに備えましょう」はユーザー指定で表示しない。
