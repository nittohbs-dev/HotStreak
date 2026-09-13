# テスト設計: カード仕込み

## トレーサビリティ

| TST-ID | 種別 | 対象 | 観点 | 関連REQ | 関連SCR/CMP | Playwright spec |
|--------|------|------|------|---------|-------------|-----------------|
| TST-seed-001 | pytest | CardSeedService | 1枚仕込み・手札減 | REQ-seed-001 | — | tests/hotstreak_core/features/card_seed/test_seed.py |
| TST-seed-002 | pytest | RacingDeck | 公開＋仕込み＝18 | REQ-seed-002 | — | tests/hotstreak_core/features/card_seed/test_deck_count.py |
| TST-seed-003 | pytest | PhaseGate | 全員揃い | REQ-seed-004 | — | tests/hotstreak_core/features/card_seed/test_advance.py |
| TST-seed-004 | E2E | 仕込み画面 | 確定で進捗更新 | REQ-seed-003 | SCR-phone-003, SCR-display-004 | tests/e2e/TST-seed-004.spec.ts |
| TST-seed-005 | API | advance | 未仕込みは 409・force-advance なし | REQ-seed-005 | — | tests/hotstreak_core/features/card_seed/test_advance_incomplete.py |

## 受け入れ条件マッピング

| REQ-ID | カバーする TST-ID |
|--------|-------------------|
| REQ-seed-001 | TST-seed-001 |
| REQ-seed-002 | TST-seed-002 |
| REQ-seed-003 | TST-seed-004 |
| REQ-seed-004 | TST-seed-003 |
| REQ-seed-005 | TST-seed-005 |

## OPEN

（なし）

枚数不一致エラーは TST-seed-002、確定後再提出拒否は API 409 でカバー。
