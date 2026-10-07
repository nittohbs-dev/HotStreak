# レース進行モック（Issue #37）

対象: SCR-display-005 / REQ-race-001〜004 の Display 表示部分。
固定シナリオでカードをめくり、効果解決と着順表示を確認します。設計書は変更していません。

```sh
python -m pip install -r src/hotstreak_display/requirements.txt
python src/hotstreak_display/screens/race.py --windowed
python src/hotstreak_display/screens/race.py --windowed --effects-demo
python -m unittest discover -s tests/hotstreak_display -p "test_race*.py" -v
```

| ファイル | 役割 |
|----------|------|
| `screens/race.py` | 起動・描画・固定サンプル列 |
| `screens/race_effects.py` | catalog の race カードを解決する |
| `screens/race_demo.py` | `--effects-demo` の 8 例自動再生 |
| `screens/race_sprites.py` | `racers-approved.png` の切り出し |

## 起動フラグ

| フラグ | 内容 |
|--------|------|
| `--windowed` | 1280×720 をウィンドウ表示。無しなら全画面 |
| `--font` | 日本語 TTF/OTF。無いと公開カードと同じ探索に落ちる |
| `--state` | `start` / `running` / `fall` / `shorten` / `finish`。既定 `start` |
| `--effects-demo` | 追加効果 8 例を約 3.2 秒間隔で自動再生 |
| `--screenshot PATH` | 起動直後の 1 フレームを PNG 保存して終了。`--effects-demo` とは同時に使ってもデモは進まない（初期 `Model` を撮る） |

Esc またはウィンドウ閉じで終了。F1・F2・R や常時の操作案内は出しません。

## 操作

- Enter（テンキー含む）で 1 枚めくる。キーリピートと長押しは無視する。演出中（`moving`）の追加入力も無視する。
- 結果画面（`finish`）の Enter で `start` に戻る。
- 矢印キーでは進まない。カード選択ピッカーはソースに残っているがキーには繋がっていない。

既定の Enter 進行は `RaceState.samples` の固定列です。catalog の 50 種すべてを順にめくるわけではありません。効果解決そのものは `data/cards/catalog.json` の `kind == "race"`（50 件）を `apply_card` が参照します。

`--effects-demo` の 8 例は ★移動・レーン変更・衝突転倒・再転倒失格・転倒中 1 マス・緑の全員移動・緑の復帰移動・方向転換です。

## 盤面と解決（このモックの実装）

- 海上の4レーン×13マス＋GOAL。初期位置は3マス目（列2）。後方にも進める。
- ★は3・8・13マス目（列2・7・12）。13マス目の先がGOAL（境界13）。
- 右上に今回のカードと効果、左上に確定した着順（ゴールと失格の両方。順位・アイコン・名前のみ。ラベルは付けない）。
- ゴールは空いている上位から、失格は空いている下位（最初は 4 位）から割り当てる。同時失格は同じ低い着順。
- 山札切れ（残り 0）で左 3 列を短縮し、残ったマスより後ろのキャラは失格。短縮中は床が沈む演出のあとで失格を確定する。
- 処理する効果: 移動・負数移動・★・方向転換・転倒・復帰・左右移動（向き基準）・緑の全員移動／復帰。
- 転倒中の数値・★移動は 1 マスに制限する。左右（swerve）は転倒中でもレーンを変える。
- 個別移動の通過マス、および横移動先にいる停止中キャラは転倒。すでに転倒していれば失格。緑は衝突せず、ゴール直前（列12）まで。
- コース外（レーン 0〜3 以外、または短縮で消えた列）は失格。3 体が終了したら残る 1 体の順位を確定する。

採用済み 4 体（ダングル／ゴブラー／マム／ハーレー）の全身透過画像を使う。素材は `assets/images/characters/racers-approved.png`（4 列 2 段）。走行 2 フレーム、向き反転、転倒と復帰を描く。

## 含まないもの

通信、無作為の山札、バーン枚の演出、投票・配当、本番の画面間遷移。山札再準備の文言は固定表示です。
このモックのみで Issue 全体の受け入れ条件を満たすものではありません。結果発表は別ランナー [`PAYOUT_MOCK.md`](PAYOUT_MOCK.md) です。
