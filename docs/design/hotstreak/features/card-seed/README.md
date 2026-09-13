# カード仕込み

## 概要

各プレイヤーが手札から **1枚** を裏向きでレーシングデッキへ仕込む。公開カードと仕込みを合わせて開始時の山は標準 **18枚**。全員仕込み完了（全員揃い）または **ラズパイ Enter** で race へ進む。

## スコープ

| 含む | 含まない |
|------|----------|
| 手札1枚の選択・仕込み確定 | マ券ドラフト（betting） |
| デッキ組成（公開＋仕込み→標準18） | バーン・めくり・効果解決（race） |
| 仕込み進捗の Display / Phone 同期 | タイマー遷移 |
| Enter による race への遷移 | 手札補充（レース間は payout） |

## 関連一覧

| 種別 | ID | 名前 |
|------|-----|------|
| 画面 | SCR-phone-003 | カード仕込み |
| 画面 | SCR-display-004 | 仕込み〜準備完了 |
| API | API-SEED-001 | 仕込み状態取得 |
| API | API-SEED-002 | 手札1枚を仕込む |
| API | API-SEED-003 | フェーズ進行（Enter） |
| CLS | CLS-HS-001 | GameSession |
| CLS | CLS-HS-002 | Player |
| CLS | CLS-HS-003 | PhaseGate |
| CLS | CLS-HS-004 | RaceCard |
| CLS | CLS-HS-005 | CardSupply |
| CLS | CLS-HS-009 | RacingDeck |
| CLS | CLS-seed-001 | CardSeedService |
| CLS | CLS-seed-002 | CardSeedApiHandler |
| CLS | CLS-seed-010 | DisplayCardSeedScreen |
| CLS | CLS-seed-011 | PhoneCardSeedScreen |
| DB | — | 永続化なし |

## 依存機能

- 先行: betting（`betting` → `card-seed`）、setup-cards（公開カード・初期手札）
- 後続: race

## 受け入れ条件

- [ ] REQ-seed-001: 各プレイヤーは手札からちょうど1枚を仕込める
- [ ] REQ-seed-002: 仕込み後、公開＋仕込み枚数が標準18になる
- [ ] REQ-seed-003: 仕込み進捗が全端末に同期される
- [ ] REQ-seed-004: 全員仕込みまたは Enter で race へ遷移する
- [ ] REQ-seed-005: Enter 時の未仕込み扱いが定義どおりである（OPEN 参照）

## 根拠で閉じた項目

| 旧ID | 決定 | 根拠 |
|------|------|------|
| OPEN-seed-003 | 公開カードのデッキ投入は **仕込み完了時** に公開＋仕込みを合わせて `RacingDeck` を組成する（card-seed 入場時ではない） | [`overview.md`](../../00-project/overview.md)、[`manual.html`](../../manual.html) ④。公式 PDF RACING「After everyone has added their card, the Dealer collects… exactly 18 cards」 |
| OPEN-seed-004 | 18枚にならない不整合は **組成失敗（エラー）**。不足をその場で補充して続行しない | setup-cards／overview 前提。公式も「should always have exactly 18」 |
| OPEN-seed-002 | 仕込み**確定後は変更不可**（裏向き提出後のやり直しなし） | [rulebook 2nd printing](https://gamers-hq.de/media/pdf/dc/37/cf/Hot_Streak_rulebook_2nd_printing.pdf) RACING「choose 1 card… face down… Never show… After everyone has added their card, the Dealer collects」。変更手順の記載なし |
| OPEN-seed-001 | **採用（暫定）**: 未仕込みのまま `POST …/advance` は **409**。自動補完なし。**force-advance API は作らない**（司会はプレイヤー完了を待つ） | 公式は全員提出前提。デジタル固有のため暫定採用（PR 確認で覆せる）。betting と同方針 |

## OPEN（確認待ち）

（なし）
