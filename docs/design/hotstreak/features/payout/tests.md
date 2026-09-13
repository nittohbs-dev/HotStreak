# テスト設計: 配当

## トレーサビリティ

| TST-ID | 種別 | 対象 | 観点 | 関連REQ | 関連SCR/CMP | Playwright spec |
|--------|------|------|------|---------|-------------|-----------------|
| TST-payout-001 | pytest | PayoutCalculator | 着順精算・4着0 | REQ-payout-001 | — | tests/hotstreak_core/features/payout/test_mascot.py |
| TST-payout-002 | pytest | PayoutCalculator | サイドベット | REQ-payout-002 | — | tests/hotstreak_core/features/payout/test_side.py |
| TST-payout-003 | pytest | PayoutCalculator | 下限0・ダブル | REQ-payout-003, 004 | — | tests/hotstreak_core/features/payout/test_floor_double.py |
| TST-payout-004 | pytest | PayoutService | レース間リセット | REQ-payout-006 | — | tests/hotstreak_core/features/payout/test_reset.py |
| TST-payout-005 | E2E | 配当画面 | 結果表示 | REQ-payout-005 | SCR-phone-005, SCR-display-006 | tests/e2e/TST-payout-005.spec.ts |

## 受け入れ条件マッピング

| REQ-ID | カバーする TST-ID |
|--------|-------------------|
| REQ-payout-001 | TST-payout-001（額表 OPEN 後に数値固定） |
| REQ-payout-002 | TST-payout-002 |
| REQ-payout-003 | TST-payout-003 |
| REQ-payout-004 | TST-payout-003 |
| REQ-payout-005 | TST-payout-005 |
| REQ-payout-006 | TST-payout-004 |

## OPEN

（なし）

同点最多は共同優勝の TST を追加する。金額マトリクスは README 観測確定表を TST データとする。補充元は既存デッキで TST-payout-004 カバー。

