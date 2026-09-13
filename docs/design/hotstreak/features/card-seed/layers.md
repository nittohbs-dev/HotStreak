# 層設計: カード仕込み

## 責務マトリクス

| 層 | CLS-ID | 責務 | 関連API |
|----|--------|------|---------|
| Domain | CLS-HS-001 | フェーズ | API-SEED-001 |
| Domain | CLS-HS-002 | 手札・seeded | API-SEED-002 |
| Domain | CLS-HS-003 | 全員揃い / Enter | API-SEED-003 |
| Domain | CLS-HS-004 | カード識別 | API-SEED-002 |
| Domain | CLS-HS-005 | 公開カード集合の参照 | REQ-seed-002 |
| Domain | CLS-HS-009 | レーシングデッキ組成 | REQ-seed-002 |
| Service | CLS-seed-001 | 仕込み・山確定・advance | API-SEED-001〜003 |
| API | CLS-seed-002 | REST / WS | API-SEED-001〜003 |
| UI | CLS-seed-010 | Display | API-SEED-001, 003 |
| UI | CLS-seed-011 | Phone | API-SEED-001, 002 |

## 主要メソッド

| 層 | メソッド | やること |
|----|----------|----------|
| Service | seedCard | 手札から1枚除去し仕込み袋へ |
| Service | buildRacingDeck | 公開＋仕込みで山を組む |
| Service | advanceSeed | race へ遷移 |

## Python パッケージ配置（実装時）

| 層 | CLS-ID | 配置先 |
|----|--------|--------|
| Domain | CLS-HS-009 | `src/hotstreak_core/domain/` |
| Service | CLS-seed-001 | `src/hotstreak_core/features/card_seed/` |
| API | CLS-seed-002 | `src/hotstreak_sync/api/card_seed/` |
| UI | CLS-seed-010 | `src/hotstreak_display/screens/card_seed.py` |
| UI | CLS-seed-011 | Phone Web（技術未確定） |
