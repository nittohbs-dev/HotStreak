# 機能設計: マ券・サイドベット

## ユースケース

| UC-ID | 操作者 | やりたいこと | 結果 |
|-------|--------|--------------|------|
| UC-betting-001 | プレイヤー | 自分の番にマ券／サイドベットを1枚取る | 在庫減・所持に追加・表裏確定 |
| UC-betting-002 | プレイヤー | 取得直後にセーフ／リスキーを選ぶ | 札面が確定する |
| UC-betting-003 | プレイヤー | 第3レースで1枚をダブル指定する | 指定札のみ配当×2 対象になる |
| UC-betting-004 | 司会（Display） | お題・手番・残り札を会場共有する | SCR-display-003 が同期更新 |
| UC-betting-005 | システム | 全員2枚取得で進行可能にする | card-seed へ遷移可能 |
| UC-betting-006 | 司会（Display） | Enter で仕込みへ進める | フェーズが `card-seed` になる |

## ビジネスルール

| BR-ID | ルール | 例外時の振る舞い |
|-------|--------|------------------|
| BR-betting-001 | フェーズ遷移にタイマーを使わない | 全員揃いまたは Enter |
| BR-betting-002 | 各プレイヤーは1レースあたりちょうど2枚取得する | 未完了で advance すると 409 |
| BR-betting-003 | 1周目は先頭から時計回り、2周目は逆順（スネーク） | — |
| BR-betting-004 | 札を取った直後にセーフ／リスキーを確定してから次手番 | 未確定のまま次手番へ進めない |
| BR-betting-005 | 在庫0の選択肢は取得不可 | API 409 / UI 無効 |
| BR-betting-006 | 第3レースのみ、2枚目取得後に所持2枚のうち1枚をダブル指定 | レース1–2では UI 非表示 |
| BR-betting-007 | ダブルは「全体×2」ではなく指定1枚のみ（マイナスも倍） | payout で適用 |
| BR-betting-008 | 第1レース先頭は unluckiest（Display が指定）。以降は時計回りローテ | — |

## 要件

### REQ-betting-001: スネークドラフト

`SnakeDraft` が手番プレイヤーを決定する。各プレイヤーが2枚取るまで交互に進行する（人数×2 手番）。

### REQ-betting-002: セーフ／リスキー

`API-BETTING-002` で ticketId と face（safe|risky）を同時に受け付ける。確定後に `betting.state` を配信する。

### REQ-betting-003: サイドベットお題

betting 入場時に、12枚山から表向き1枚を `SideBetPrompt` として提示する（シャッフル済み）。レース間は前札を山底へ回し次を公開。お題文面の全文はデータ側。

### REQ-betting-004: 在庫

初期山: マスコット4色×各3枚（計12）＋ YES／NO サイド券計6枚。各山は Safe 上・小さい札を上。手番は選んだ山の一番上のみ取得可。在庫0は選択不可。

### REQ-betting-005: 第3ダブル

`raceIndex === 3` かつ所持2枚のとき `API-BETTING-003` で1枚を doubleTicketId に指定する。未指定のまま advance すると 409。

### REQ-betting-006: フェーズ遷移

全員が2枚取得済みかつ第3レースは全員 double 指定済みのとき、自動または Enter で `betting` → `card-seed`。

### REQ-betting-007: Enter 時の未完了（採用）

1. `API-BETTING-004`（advance）は、全員が2枚取得済みかつ第3レースは全員 double 指定済みのときのみ成功する。
2. 未完了のまま Enter／advance → **409**（自動で札を補完しない）。
3. **force-advance API は設けない**。司会はプレイヤー完了を待つ。

### REQ-betting-008: 配当額の扱い

チケット文言の verbatim 転載はしない。UI はセーフ／リスキーを必須表示し、金額は `features/payout/README.md` の観測確定表（実装データ）を参照。

### REQ-betting-009: ドラフト先頭

第1レースは Display が unluckiest 相当の先頭 `playerId` を指定。以降レースは時計回りにローテ。

## OPEN（詳細）

（なし）
