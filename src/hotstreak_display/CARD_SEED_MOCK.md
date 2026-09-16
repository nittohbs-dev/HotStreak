# カード仕込み〜準備完了モック（Issue #35）

対象: SCR-display-004 / REQ-seed-002・003・004のDisplay表示部分。
既存の公開カード画面の描画部品を利用します。他画面・設計書は変更していません。

```sh
python -m pip install -r src/hotstreak_display/requirements.txt
python src/hotstreak_display/screens/card_seed.py --windowed
```

- `--windowed` なしで全画面、Escで終了。
- 左右キーで固定表示例「仕込み待ち／仕込み中／カード束確定／準備完了」を切り替え。
- 準備完了の見本でEnterを押すと、レースへの進行確認メッセージを表示。レース画面は未実装で、そのまま留まります。
- 仕込み中のEnterは何も変更しません。タイマーで勝手に進みません。
- `--state 0`〜`--state 3`で表示例指定、`--screenshot output.png`でPNG保存。
- 日本語フォントが見つからない場合は `--font path/to/font.ttf` を指定。

6人・18枚の固定データによるモックです。裏面だけを表示し、手札・仕込み内容は扱いません。
仕込み途中の18枚は完成時の見込み表示です。カード抽選、仕込み処理、デッキ組成、通信、レース進行は実装しません。
今日の指示に従い、本番APIとの接続やゲーム処理は両側のモック完成後に行います。

検証: `python -m unittest discover -s tests/hotstreak_display -v`
