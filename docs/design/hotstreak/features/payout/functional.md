# 機能設計: 配当

## ユースケース

| UC-ID | 操作者 | やりたいこと | 結果 |
|-------|--------|--------------|------|
| UC-payout-001 | システム | 着順と札面から精算する | 各 Player.balance 更新 |
| UC-payout-002 | プレイヤー | 自分の払戻と全体順位を見る | SCR-phone-005 |
| UC-payout-003 | 司会（Display） | 着順を会場共有する | SCR-display-006 |
| UC-payout-004 | 司会（Display） | Enter で次へ進める | betting または lobby |

## ビジネスルール

| BR-ID | ルール | 例外時の振る舞い |
|-------|--------|------------------|
| BR-payout-001 | タイマー遷移なし。次へは Enter | — |
| BR-payout-002 | マスコットマ券は着順に応じ札面。4着 $0。額は README 観測確定表 | — |
| BR-payout-003 | サイドベットは YES/NO 成否×tier。額は README 観測確定表（Safe 正解 10/7/5、Risky 正解 15/12/10・不正解 −5） | — |
| BR-payout-004 | リスキー外れは損失。所持金下限 $0 | — |
| BR-payout-005 | 第3は指定1枚のみ×2（マイナスも倍） | — |
| BR-payout-006 | レース1–2後: マ券返却・お題更新・**既存レーシングデッキから**各1枚補充・コース／マスコットリセット・先頭ローテ | — |
| BR-payout-007 | レース3後: 最多所持金が勝ち。同点最多は**共同優勝**。Enter でロビーへ | — |

## 要件

### REQ-payout-001〜004: 精算

`PayoutCalculator` が race の着順・sideBetOutcome・各 BetTicket（face・double）から delta を算出し balance に加算（下限0）。

### REQ-payout-005: 表示

`payout.state` で着順・個人内訳・プレイヤー順位を配信。

### REQ-payout-006: Enter

- raceIndex < 3: レース間リセット後 `betting`
- raceIndex === 3: phase=`lobby`（SCR-phone-001 / SCR-display-001）。同点最多は**共同優勝**（勝者配列を複数可）

## OPEN（詳細）

（なし）
