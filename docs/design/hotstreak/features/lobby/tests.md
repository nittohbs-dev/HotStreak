# テスト設計: 参加・ロビー

## トレーサビリティ

| TST-ID | 種別 | 対象 | 観点 | 関連REQ | 関連SCR/CMP | Playwright spec |
|--------|------|------|------|---------|-------------|-----------------|
| TST-lobby-001 | pytest | LobbyService | 参加・名前・$10 付与 | REQ-lobby-002, 003, 004 | — | tests/hotstreak_core/features/lobby/test_join_name.py |
| TST-lobby-002 | pytest | LobbyService | 人数制限 | REQ-lobby-005 | — | tests/hotstreak_core/features/lobby/test_limits.py |
| TST-lobby-003 | pytest | PhaseGate | 全員揃いで advance | REQ-lobby-006 | — | tests/hotstreak_core/features/lobby/test_advance_all_ready.py |
| TST-lobby-004 | pytest | LobbyService | Enter + プレースホルダ名 | REQ-lobby-007 | — | tests/hotstreak_core/features/lobby/test_advance_enter.py |
| TST-lobby-005 | E2E | ロビー画面 | Phone 確定 → Display 一覧更新 | REQ-lobby-003 | SCR-phone-001, SCR-display-001 | tests/e2e/TST-lobby-005.spec.ts |

種別: **E2E** = Playwright E2E、`CT` = Playwright Component Test

## E2E シナリオ

| TST-ID | 画面 | 操作 | 期待結果 |
|--------|------|------|----------|
| TST-lobby-005 | SCR-phone-001 | 名前確定 | Display の参加者一覧に同名が表示される |

## コンポーネントシナリオ

| CMP-ID | TST-ID | 観点 | 期待結果 |
|--------|--------|------|----------|
| CMP-lobby-011 | （実装時） | 空名で確定 | エラー表示・API 未呼び出し |
| CMP-lobby-003 | （実装時） | players 更新 | 人数とリストが一致 |

## バックエンド（pytest — Playwright 対象外）

| TST-ID | 層 | 観点 | 関連REQ |
|--------|-----|------|---------|
| TST-lobby-001 | Service | join と name で balance=10 | REQ-lobby-004 |
| TST-lobby-002 | Service | 9人目 join 拒否・2人で advance 拒否 | REQ-lobby-005 |
| TST-lobby-003 | Domain | 全員 nameReady で遷移可能 | REQ-lobby-006 |
| TST-lobby-004 | Service | 未確定者にプレースホルダ名 | REQ-lobby-007 |
| TST-lobby-006 | API | lobby 後の join は 409 | REQ-lobby-008 |

## 受け入れ条件マッピング

| REQ-ID | カバーする TST-ID |
|--------|-------------------|
| REQ-lobby-001 | （Display 起動テスト・実装時） |
| REQ-lobby-002 | TST-lobby-001 |
| REQ-lobby-003 | TST-lobby-001, TST-lobby-005 |
| REQ-lobby-004 | TST-lobby-001 |
| REQ-lobby-005 | TST-lobby-002 |
| REQ-lobby-006 | TST-lobby-003, TST-lobby-004 |
| REQ-lobby-007 | TST-lobby-004 |
| REQ-lobby-008 | TST-lobby-006 |
