# HotStreak

予測不能なドタバタ劇！ボードゲーム『ホットストリーク』の会場ディスプレイ＋スマホ版。
3〜8人が同じWi-FiからQRで参加し、マ券選択・カード仕込み・レース・精算を3レース遊べます。

## 起動

Python環境を管理する `uv` がある場合、リポジトリのルートで実行します。
必要なPython 3.12と依存ライブラリは自動で用意します。

```sh
./play.sh --windowed
```

ウィンドウを閉じるかEscで、会場画面と同時起動したサーバーが終了します。
全画面で起動する場合は `--windowed` を省略します。

`uv` を使わない場合はPython 3.11以上の仮想環境で実行できます。

```sh
python -m pip install -r requirements.txt
PYTHONPATH=src python -m hotstreak_display.app --windowed
```

## 遊び方

1. 会場PCとスマホを同じWi-Fiにつなぎ、会場画面のQRを読み取ります。
2. 全員が参加してから各スマホで名前を確定します。3人以上が全員確定すると公開カードへ進みます。会場のEnterでも開始でき、未入力の名前は参加順に補います。
3. 公開カード画面で左右キーを使い、第1レースのマ券選択の先頭を選びます。Enterでマ券選択へ進みます。
4. スマホで自分の番に札を選び、セーフ／リスキーを決めて確定します。全員2枚、第3レースはダブルにする1枚も指定したら、会場のEnterで仕込みへ進みます。
5. 各スマホで手札3枚から1枚を選びます。全員が仕込んだら会場のEnterでレース開始です。
6. 会場のEnterでカードを1枚ずつめくります。レースが終わると着順・払戻・所持金順位が表示されます。
7. Enterで次レースへ。3レース終了時は最多所持金が総合優勝、同点は共同優勝です。最後のEnterで受付へ戻ります。

進行にタイマーは使いません。未完了のマ券や仕込みをEnterで勝手に補完することもありません。

## 接続できない場合

会場サーバーはTCPポート8000を使用します。QRが別のネットワークのIPになる場合は指定してください。

```sh
./play.sh --windowed --public-host 192.168.1.10
./play.sh --windowed --port 8001
```

スマホでは `127.0.0.1` を使わず、QRに表示された会場PCのIPを開いてください。
会場PCのファイアウォールと、Wi-Fiの端末間通信設定も確認してください。
日本語フォントが見つからない場合は `--font /path/to/font.ttf` を指定できます。

対局データはメモリ上に保存され、アプリ終了で失われます。
通信切断時は自動で再接続します。ロビーページ自体の再読み込みは設計どおり新規参加となります。
Raspberry Piの実機・物理Enterボタンは別途実機確認が必要です。

## 開発・検証

```sh
PYTHONPATH=src uv run --python 3.12 --with-requirements requirements.txt --with pytest --with httpx python -m pytest tests/hotstreak_core tests/hotstreak_display -q
node --test tests/hotstreak_phone/*.test.js
```

`tests/hotstreak_core/test_playable_game.py` は3〜8人の各人数で、実RESTを使って3レースと次の受付まで検証します。
`tests/hotstreak_display/test_live_game.py` は実ゲーム状態で全会場画面を描画します。
デモは各画面の見た目を確認する用途として残しています。実プレイは上記の会場アプリを使ってください。

設計書は [`docs/design/hotstreak/`](docs/design/hotstreak/)、ルールは [`.agents/AGENTS.md`](.agents/AGENTS.md) が正本です。
設計把握ビューアは [`tools/spec-browser/README.md`](tools/spec-browser/README.md)、カード素材は [`assets/README.md`](assets/README.md) を参照してください。
