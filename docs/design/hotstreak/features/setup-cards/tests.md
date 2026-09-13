# テスト設計: 公開カード準備

## トレーサビリティ

| TST-ID | 種別 | 対象 | 観点 | 関連REQ | 関連SCR/CMP | Playwright spec |
|--------|------|------|------|---------|-------------|-----------------|
| TST-setup-001 | pytest | SetupCardsService | 入場時に公開＋手札配布 | REQ-setup-001, 004 | — | tests/hotstreak_core/features/setup_cards/test_deal.py |
| TST-setup-002 | pytest | SetupCardsService | スターター4＋人数表 | REQ-setup-002, 003, 007 | — | tests/hotstreak_core/features/setup_cards/test_face_up_counts.py |
| TST-setup-003 | pytest | CardSupply | 重複なし | REQ-setup-001 | — | tests/hotstreak_core/features/setup_cards/test_no_dup.py |
| TST-setup-004 | pytest | SetupCardsService | Enter で betting | REQ-setup-006 | — | tests/hotstreak_core/features/setup_cards/test_advance.py |
| TST-setup-005 | E2E | 公開カード画面 | setup.state → Display 表示 | REQ-setup-005 | SCR-display-002 | tests/e2e/TST-setup-005.spec.ts |

種別: **E2E** = Playwright E2E、`CT` = Playwright Component Test

## E2E シナリオ

| TST-ID | 画面 | 操作 | 期待結果 |
|--------|------|------|----------|
| TST-setup-005 | SCR-display-002 | lobby 完了後に待機 | 公開カード枚数が人数表どおり表示される |

## コンポーネントシナリオ

| CMP-ID | TST-ID | 観点 | 期待結果 |
|--------|--------|------|----------|
| CMP-setup-003 | （実装時） | faceUpCards 更新 | グリッド枚数が一致 |

## バックエンド（pytest — Playwright 対象外）

| TST-ID | 層 | 観点 | 関連REQ |
|--------|-----|------|---------|
| TST-setup-001 | Service | 各手札3枚・dealt=true | REQ-setup-001, 004 |
| TST-setup-002 | Service | 3人15公開／8人10公開 | REQ-setup-003, 007 |
| TST-setup-003 | Domain | 公開と手札で cardInstance 重複なし | REQ-setup-001 |
| TST-setup-004 | Service | advance で phase=betting | REQ-setup-006 |
| TST-setup-006 | API | 未配布で advance は 409 | REQ-setup-006 |

## 受け入れ条件マッピング

| REQ-ID | カバーする TST-ID |
|--------|-------------------|
| REQ-setup-001 | TST-setup-001, TST-setup-003 |
| REQ-setup-002 | TST-setup-002 |
| REQ-setup-003 | TST-setup-002, TST-setup-005 |
| REQ-setup-004 | TST-setup-001 |
| REQ-setup-005 | TST-setup-005 |
| REQ-setup-006 | TST-setup-004, TST-setup-006 |
| REQ-setup-007 | TST-setup-002 |
