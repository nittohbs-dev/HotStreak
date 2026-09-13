# 配当

## 概要

レース着順に基づきマ券・サイドベットを精算し、所持金を更新する（最低 $0）。Display に着順、Phone に個人払戻とプレイヤー順位を示す。レース1–2は **レース間リセット** の後に betting へ、レース3は最終所持金で勝敗を確定する。次フェーズへは原則 **ラズパイ Enter**。

## スコープ

| 含む | 含まない |
|------|----------|
| マ券・サイドベットの精算 | レース演算そのもの（race） |
| 所持金更新・順位表示 | マ券ドラフト操作（betting） |
| レース間リセット（札戻し・お題更新・手札補充・先頭ローテ） | タイマー遷移 |
| Enter による次レース／試合終了 | 永続ランキング |

## 関連一覧

| 種別 | ID | 名前 |
|------|-----|------|
| 画面 | SCR-phone-005 | 配当 |
| 画面 | SCR-display-006 | 着順・結果 |
| API | API-PAYOUT-001 | 配当状態取得 |
| API | API-PAYOUT-002 | フェーズ進行（Enter） |
| CLS | CLS-HS-001 | GameSession |
| CLS | CLS-HS-002 | Player |
| CLS | CLS-HS-003 | PhaseGate |
| CLS | CLS-HS-006 | BetTicket |
| CLS | CLS-HS-013 | PayoutCalculator |
| CLS | CLS-payout-001 | PayoutService |
| CLS | CLS-payout-002 | PayoutApiHandler |
| CLS | CLS-payout-010 | DisplayPayoutScreen |
| CLS | CLS-payout-011 | PhonePayoutScreen |
| DB | — | 永続化なし |

## 依存機能

- 先行: race（着順・サイドベット成否フラグ）
- 後続: betting（レース1–2）または試合終了（レース3）

## 受け入れ条件

- [ ] REQ-payout-001: 着順に応じてマスコットマ券を精算する（4着 $0）
- [ ] REQ-payout-002: サイドベット YES/NO を精算する
- [ ] REQ-payout-003: リスキー外れの損失を適用し所持金は最低 $0
- [ ] REQ-payout-004: 第3のダブル指定札のみ損益×2
- [ ] REQ-payout-005: Display 着順・Phone 個人明細が同期表示される
- [ ] REQ-payout-006: Enter でレース間リセット後 betting、または試合終了へ

## 根拠で閉じた項目

| 旧ID | 決定 | 根拠 |
|------|------|------|
| OPEN-payout-001 | チケット**文言の verbatim 転載はしない**。数値パラメータ表のみ設計に載せる | overview 転載スコープ外。公式 PDF PAYOUTS「amounts listed on their betting tickets」 |
| OPEN-payout-002 | 面額マトリクスは下記**観測確定表**を実装初期正本とする（マスコット／サイドとも top・mid・bot） | GeekDad 写真 [MascotBets](https://geekdad.com/wp-content/uploads/2025/09/HotStreak-MascotBets.jpg)・[SideBetTickets](https://geekdad.com/wp-content/uploads/2025/09/HotStreak-SideBetTickets.jpg)。Shelf Gamer [Risky top 例](https://shelfgamer.com/wp-content/uploads/2026/01/review-hot-streak-risky-dangle-bet.jpg)（15/5/2）で整合。公式 PDF 例「1着 $11」＝ Mid Risky 1着と一致 |
| OPEN-payout-003 | レース間の手札補充は **既存のレーシングデッキから各1枚**（新規カードではない）。山をシャッフルして配る | [rulebook](https://gamers-hq.de/media/pdf/dc/37/cf/Hot_Streak_rulebook_2nd_printing.pdf) THE 2ND RACE「shu!es the racing deck and deals 1 face down card from it… from the existing racing deck, not new cards!」 |
| OPEN-payout-004 | レース3後 Enter でロビーへ（既存決定） | wireframes／manual（前回クローズ） |
| OPEN-payout-005 | **採用（暫定）**: レース3終了時に所持金が同点最多のプレイヤーが複数いる場合は **共同優勝**（追加タイブレーク無し）。Display／Phone は同点優勝者を複数表示 | 公式は「most cash」のみでタイブレークなし。暫定採用（PR 確認で覆せる） |

### 観測確定額表（OPEN-payout-002・数値のみ）

| 種別 | 面 | tier | 条件 | 額（$） |
|------|----|------|------|---------|
| マスコット | Safe | top | 1 / 2 / 3 着 | 10 / 7 / 5 |
| マスコット | Safe | mid | 1 / 2 / 3 着 | 7 / 5 / 3 |
| マスコット | Safe | bot | 1 / 2 / 3 着 | 5 / 3 / 2 |
| マスコット | Safe | いずれ | 4 着 | 0 |
| マスコット | Risky | top | 1 / 2 / 3 着 | 15 / 5 / 2 |
| マスコット | Risky | mid | 1 / 2 / 3 着 | 11 / 3 / 1 |
| マスコット | Risky | bot | 1 / 2 / 3 着 | 8 / 2 / 0 |
| マスコット | Risky | いずれ | 4 着 | 0 |
| サイド | Safe | top / mid / bot | 正解 | 10 / 7 / 5 |
| サイド | Safe | いずれ | 不正解 | 0 |
| サイド | Risky | top / mid / bot | 正解 | 15 / 12 / 10 |
| サイド | Risky | いずれ | 不正解 | −5 |

注: 二次レビュー文面の「サイド Safe は常に $10」は **top のみ**の簡略だった。写真で mid/bot も確認。

## OPEN（確認待ち）

（なし）

