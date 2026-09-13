# マ券・サイドベット

## 概要

スネークドラフトで各プレイヤーがマ券またはサイドベットを **2枚** 取得し、取得直後に **セーフ／リスキー** を選ぶ。第3レースのみ、所持2枚のうち **1枚だけ** 配当ダブルを指定する。全員2枚取得（全員揃い）または **ラズパイ Enter** で card-seed へ進む。

## スコープ

| 含む | 含まない |
|------|----------|
| スネークドラフト・在庫減・手番進行 | 公開カード配布（setup-cards） |
| セーフ／リスキー選択 | カード仕込み・レース演算 |
| サイドベットお題の提示・YES/NO 札 | 配当の金額計算（payout） |
| 第3レースの1枚ダブル指定 | タイマーによる遷移 |

## 関連一覧

| 種別 | ID | 名前 |
|------|-----|------|
| 画面 | SCR-phone-002 | マ券ドラフト |
| 画面 | SCR-display-003 | マ券ドラフト共有 |
| API | API-BETTING-001 | ベット状態取得 |
| API | API-BETTING-002 | 札取得＋表裏確定 |
| API | API-BETTING-003 | 第3ダブル指定 |
| API | API-BETTING-004 | フェーズ進行（Enter） |
| CLS | CLS-HS-001 | GameSession |
| CLS | CLS-HS-002 | Player |
| CLS | CLS-HS-003 | PhaseGate |
| CLS | CLS-HS-006 | BetTicket |
| CLS | CLS-HS-007 | SideBetPrompt |
| CLS | CLS-HS-008 | SnakeDraft |
| CLS | CLS-betting-001 | BettingService |
| CLS | CLS-betting-002 | BettingApiHandler |
| CLS | CLS-betting-010 | DisplayBettingScreen |
| CLS | CLS-betting-011 | PhoneBettingScreen |
| DB | — | 永続化なし（対局中メモリ） |

## 依存機能

- 先行: setup-cards（フェーズ `setup-cards` → `betting`。公開カードは参照のみ）
- 後続: card-seed

## 受け入れ条件

- [ ] REQ-betting-001: スネーク順（1周目時計回り・2周目逆順）で各2枚取得できる
- [ ] REQ-betting-002: 取得直後にセーフ／リスキーを選べる
- [ ] REQ-betting-003: サイドベットお題が Display / Phone に同期表示される
- [ ] REQ-betting-004: 在庫0の札は選択不可
- [ ] REQ-betting-005: 第3レースで所持2枚のうち1枚だけダブル指定できる
- [ ] REQ-betting-006: 全員2枚取得または Enter で card-seed へ遷移する
- [ ] REQ-betting-007: Enter 時の未完了手番の扱いが定義どおりである（OPEN 参照）

## 根拠で閉じた項目

| 旧ID | 決定 | 根拠 |
|------|------|------|
| OPEN-betting-005 | チケット**文言の verbatim 転載はしない**。画面は表裏表示を必須。**数値パラメータは payout 観測確定表**（`features/payout/README.md`）を参照 | overview 転載スコープ外。payout OPEN-payout-002 クローズ |
| OPEN-betting-001 | 第1レース先頭は **unluckiest player（一番運の悪い人）**。以降は時計回りに先頭ローテ。デジタルでは Display（司会）が先頭 `playerId` を指定して記録する（物理の合意を代替） | [Hot Streak rulebook 2nd printing](https://gamers-hq.de/media/pdf/dc/37/cf/Hot_Streak_rulebook_2nd_printing.pdf) SETUP §9「The unluckiest player goes first」、THE 2ND RACE「Rotate who drafts first, moving one player clockwise」。公式 How to play: https://www.cmyk.games/products/hot-streak |
| OPEN-betting-002 | 山は **6スタック**（マスコット色4＋YES＋NO）。マスコット券 **12枚**（各色 top/middle/bottom の3枚）、サイド券 **6枚**。Safe 面を上、小さい札（高配当側）を上に積む | 同 PDF SETUP §4「6 stacks, Safe side up, smaller size tickets on top」、CONTENTS「12 mascot bet tickets / 6 side bet tickets」。Misut Meeple 部品表も同数: https://misutmeeple.com/en/2026/02/review-hot-streak/ |
| OPEN-betting-003 | YES 山と NO 山は別。各手番は **いずれか1山の一番上** を取る。残りがあれば複数人が同じ YES/NO を取れる（同時取得ではなく順次） | 同 PDF BETTING「drafts one betting ticket from the top of whichever stack they choose」。SETUP §6「between the YES and NO betting tickets」 |
| OPEN-betting-006 | お題は **12枚のサイドベットカード**をシャッフルし、1枚を表向き提示。レース後は前のお題を山の下へ回し次を公開。個別のお題文面は設計書に全文列挙しない（データ化） | 同 PDF CONTENTS「12 side bet cards」、SETUP §6、THE 2ND RACE「previous side bet on the bottom… revealing a new side bet」 |
| OPEN-betting-004 | **採用（暫定）**: 未完了のまま `POST …/advance` は **409**。自動補完なし。**force-advance API は作らない**（司会はプレイヤー完了を待つ）。全員2枚＋第3は double 指定済みで advance／全員揃い成功 | 公式はスネーク完了前提。デジタル固有のため暫定採用（PR 確認で覆せる） |

## OPEN（確認待ち・仕様未確定）

（なし。Enter 未完了は上記どおり暫定採用済み）
