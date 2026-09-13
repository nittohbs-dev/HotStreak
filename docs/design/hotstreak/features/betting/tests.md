# テスト設計: マ券・サイドベット

## トレーサビリティ

| TST-ID | 種別 | 対象 | 観点 | 関連REQ | 関連SCR/CMP | Playwright spec |
|--------|------|------|------|---------|-------------|-----------------|
| TST-betting-001 | pytest | SnakeDraft | スネーク順 | REQ-betting-001 | — | tests/hotstreak_core/features/betting/test_snake.py |
| TST-betting-002 | pytest | BettingService | 表裏確定・在庫減 | REQ-betting-002, 004 | — | tests/hotstreak_core/features/betting/test_pick.py |
| TST-betting-003 | pytest | BettingService | 第3ダブル | REQ-betting-005 | — | tests/hotstreak_core/features/betting/test_double.py |
| TST-betting-004 | pytest | PhaseGate | 全員揃い advance | REQ-betting-006 | — | tests/hotstreak_core/features/betting/test_advance.py |
| TST-betting-005 | E2E | マ券画面 | 手番で札取得が Display に反映 | REQ-betting-001, 003 | SCR-phone-002, SCR-display-003 | tests/e2e/TST-betting-005.spec.ts |

## E2E シナリオ

| TST-ID | 画面 | 操作 | 期待結果 |
|--------|------|------|----------|
| TST-betting-005 | SCR-phone-002 | 手番で1枚確定 | Display の手番・残札が更新される |

## バックエンド（pytest）

| TST-ID | 層 | 観点 | 関連REQ |
|--------|-----|------|---------|
| TST-betting-001 | Domain | 1周目順・2周目逆順 | REQ-betting-001 |
| TST-betting-002 | Service | face 必須・在庫0拒否 | REQ-betting-002, 004 |
| TST-betting-003 | Service | レース1で double 拒否・レース3で1枚のみ | REQ-betting-005 |
| TST-betting-004 | Service | 全員2枚で card-seed | REQ-betting-006 |
| TST-betting-006 | API | 他者番の pick は 403 | REQ-betting-001 |
| TST-betting-007 | API | 未完了 advance は 409・force-advance なし | REQ-betting-007 |

## 受け入れ条件マッピング

| REQ-ID | カバーする TST-ID |
|--------|-------------------|
| REQ-betting-001 | TST-betting-001, TST-betting-005 |
| REQ-betting-002 | TST-betting-002 |
| REQ-betting-003 | TST-betting-005 |
| REQ-betting-004 | TST-betting-002 |
| REQ-betting-005 | TST-betting-003 |
| REQ-betting-006 | TST-betting-004 |
| REQ-betting-007 | TST-betting-007 |

## OPEN

（なし）

※ 配当額表示の E2E は payout 観測確定表を TST データとする。
