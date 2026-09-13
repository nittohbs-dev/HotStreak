# テスト設計: レース進行

## トレーサビリティ

| TST-ID | 種別 | 対象 | 観点 | 関連REQ | 関連SCR/CMP | Playwright spec |
|--------|------|------|------|---------|-------------|-----------------|
| TST-race-001 | pytest | RaceEngine | バーン3枚後めくり | REQ-race-001 | — | tests/hotstreak_core/features/race/test_burn.py |
| TST-race-002 | pytest | RaceEngine | 効果適用（種別スモーク） | REQ-race-002 | — | tests/hotstreak_core/features/race/test_effects.py |
| TST-race-003 | pytest | Course | 短縮と DQ | REQ-race-003 | — | tests/hotstreak_core/features/race/test_shorten.py |
| TST-race-004 | pytest | RaceEngine | 3体終了で着順 | REQ-race-004 | — | tests/hotstreak_core/features/race/test_finish.py |
| TST-race-005 | E2E | 観戦 | race.state で順位更新 | REQ-race-005 | SCR-phone-004 | tests/e2e/TST-race-005.spec.ts |

## 受け入れ条件マッピング

| REQ-ID | カバーする TST-ID |
|--------|-------------------|
| REQ-race-001 | TST-race-001 |
| REQ-race-002 | TST-race-002（効果スモーク。詳細は英語ルール準拠データ） |
| REQ-race-003 | TST-race-003 |
| REQ-race-004 | TST-race-004 |
| REQ-race-005 | TST-race-005 |
| REQ-race-006 | （実装時 CT） |

## OPEN

なし（マス長はワイヤー数え上げで確定）。物理14行準拠に切り替える場合のみ Course TST を更新。
