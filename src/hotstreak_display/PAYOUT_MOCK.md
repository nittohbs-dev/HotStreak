# 着順・結果モック（Issue #42）

対象: SCR-display-006。既存の背景・金色の枠と、レースと同じ採用済み全身素材を使う 1280×720 の固定表示例です。
設計書は変更しません。通信・精算・画面間の接続は未実装です。
このモックだけで Issue 全体の受け入れ条件を満たすものではありません。

```sh
python -m pip install -r src/hotstreak_display/requirements.txt
python src/hotstreak_display/screens/payout.py --windowed
python src/hotstreak_display/screens/payout.py --windowed --race 3 --state dq
```

Display 側の自動テストはレースモック（`test_race*.py`）のみです。この画面の回帰は目視と `--screenshot` です。

| フラグ | 内容 |
|--------|------|
| `--windowed` | ウィンドウ表示。無しなら全画面 |
| `--font` | 日本語 TTF/OTF |
| `--race 1`〜`3` | レース番号。フッタ案内が変わる。既定 1 |
| `--state` | `normal` / `dq` / `tie`。既定 `normal` |
| `--screenshot PATH` | PNG 保存して終了 |

- `--state tie` は共同優勝例のため、`--race` を無視してレース 3 として描く。
- 表示は時間経過で進まない。状態は起動引数で選ぶ。
- Enter で「進行確認の表示例 / 次画面への接続は未実装」に差し替える。1・2 レースの初期フッタは次レースのマ券、3 レースは参加受付。実際には [`BETTING_MOCK.md`](BETTING_MOCK.md) にもロビー Display にも移らない。
- Esc・矢印キーでは遷移しない。終了はウィンドウを閉じる。
- 表彰台と 4 位／失格欄は `race_sprites.py` と `assets/images/characters/racers-approved.png`。
- FINISH と「次のレースに備えましょう」は出さない。金額は計算しない（固定ラベルのみ）。
