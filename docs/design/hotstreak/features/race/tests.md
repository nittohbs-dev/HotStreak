# テスト設計: レース進行

## トレーサビリティ

| TST-ID | 種別 | 対象 | 観点 | 関連REQ | 関連SCR/CMP | Playwright spec |
|--------|------|------|------|---------|-------------|-----------------|
| TST-race-001 | pytest | RaceEngine | バーン3枚後めくり | REQ-race-001 | — | tests/hotstreak_core/features/race/test_burn.py |
| TST-race-002 | pytest | RaceEngine | 効果適用（種別スモーク） | REQ-race-002 | — | tests/hotstreak_core/features/race/test_effects.py |
| TST-race-003 | pytest | Course | 短縮と DQ | REQ-race-003 | — | tests/hotstreak_core/features/race/test_shorten.py |
| TST-race-004 | pytest | RaceEngine | 3体終了で着順 | REQ-race-004 | — | tests/hotstreak_core/features/race/test_finish.py |
| TST-race-005 | E2E | 観戦 | race.state で順位更新 | REQ-race-005 | SCR-phone-004 | tests/e2e/TST-race-005.spec.ts |
| TST-race-006 | pytest | Display自動進行 | OFF開始、Enterの開始・停止・再開、演出完了＋0.5秒、長押し抑止 | REQ-race-008 | SCR-display-005 / CMP-race-001 | tests/hotstreak_display/test_live.py |
| TST-race-007 | pytest | Display進行要求 | 最大1件、要求中・演出中・待機中の停止、停止と送信が同時なら停止優先 | REQ-race-008 | SCR-display-005 / CMP-race-001 | tests/hotstreak_display/test_live.py |
| TST-race-008 | pytest | Display停止境界 | 終了・通信失敗・409・フォーカス喪失でOFF、復帰・新レースで勝手に再開しない | REQ-race-008 | SCR-display-005 / CMP-race-001 | tests/hotstreak_display/test_live.py |
| TST-race-009 | 手動E2E | 実セッション | Enterだけで開始・演出中停止・再開・3レース完走、Phone同期、配当操作の分離 | REQ-race-008 | SCR-display-005 / SCR-phone-004 | — |

## 受け入れ条件マッピング

| REQ-ID | カバーする TST-ID |
|--------|-------------------|
| REQ-race-001 | TST-race-001 |
| REQ-race-002 | TST-race-002（効果スモーク。詳細は英語ルール準拠データ） |
| REQ-race-003 | TST-race-003 |
| REQ-race-004 | TST-race-004 |
| REQ-race-005 | TST-race-005 |
| REQ-race-006 | （実装時 CT） |
| REQ-race-008 | TST-race-006〜009 |

## OPEN

なし（マス長はワイヤー数え上げで確定）。物理14行準拠に切り替える場合のみ Course TST を更新。
