# マ券ドラフト共有モック — Issue #31

作成画面: SCR-display-003（会場ディスプレイ）。サイドベットのお題・手番・参加者の取得状況・残りマ券を表示します。
公開カードと同じ背景・書体・マスコット描画を使用し、既存の公開カード実装と設計書は変更していません。

## 起動

リポジトリのルートで、既存Displayの依存パッケージをインストールします。

```sh
python -m pip install -r src/hotstreak_display/requirements.txt
python src/hotstreak_display/screens/betting.py --windowed
```

`--windowed` を外すと全画面です。日本語フォントが自動検出できない場合は `--font path/to/font.ttf` を指定します。

```sh
python src/hotstreak_display/screens/betting.py --from-setup
```

`--from-setup` は既存の公開カードデモからEnterでマ券ドラフトモックに移る、表示確認専用のランナーです。
公開カードの単独起動や実サーバ用処理は変更していません。ロビーやカード仕込み画面は含みません。

## 確認操作

- 左右キー: 固定の表示例を切り替え（開始前／ドラフト中／全員選択済み／第3レースのダブル待ち）。
- Enter: 全員選択済みの見本では進行確認メッセージ。それ以外では待機案内。次画面は作成せず、この画面に留まります。
- Esc: 終了。
- `--state 0`〜`--state 3`: 表示例を指定して起動。
- `--screenshot output.png`: 現在の表示例をPNG保存して終了。

操作はモックの確認用です。参加者名・枚数・在庫数は固定の見本です。手番計算・購入・在庫更新はしません。
お題文はカタログの `event_disqualified`（「1体以上が失格する？」）を表示し、カード絵とマスコットアイコンは `CardAssets` から読みます。色ラベルは青／オレンジ／サーモン／黄です。
通信、抽選、スネーク手番の演算、配当計算は実装していません。
スマホでの選択UIは [`src/hotstreak_phone/README.md`](../hotstreak_phone/README.md) 側です。REQ-betting-003/006のうち表示と進行可否の見た目を確認し、実接続は後工程で行います。

## 検証

```sh
python -m unittest discover -s tests/hotstreak_display -v
```

各表示例・Enterの反応・固定データが操作で書き換わらないことをPythonで検証し、Pygameの画像出力で目視確認します。
