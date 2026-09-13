# 層設計: 配当

## 責務マトリクス

| 層 | CLS-ID | 責務 | 関連API |
|----|--------|------|---------|
| Domain | CLS-HS-001 | フェーズ・raceIndex | API-PAYOUT-001 |
| Domain | CLS-HS-002 | balance 更新 | 精算 |
| Domain | CLS-HS-003 | Enter 進行 | API-PAYOUT-002 |
| Domain | CLS-HS-006 | 札面・ダブル | 精算 |
| Domain | CLS-HS-013 | 損益計算 | 精算 |
| Service | CLS-payout-001 | 精算・リセット・advance | API-PAYOUT-001, 002 |
| API | CLS-payout-002 | REST / WS | API-PAYOUT-001, 002 |
| UI | CLS-payout-010 | Display | API-PAYOUT-001, 002 |
| UI | CLS-payout-011 | Phone | API-PAYOUT-001 |

## 主要メソッド

| 層 | メソッド | やること |
|----|----------|----------|
| Service | settleRace | 着順・札から balance 更新 |
| Service | resetBetweenRaces | 札戻し・お題・手札補充・ローテ |
| Service | advancePayout | 次 betting または ended |
| Domain | calcTicketDelta | 観測確定額表に従う |

## Python パッケージ配置（実装時）

| 層 | CLS-ID | 配置先 |
|----|--------|--------|
| Domain | CLS-HS-013 | `src/hotstreak_core/domain/` |
| Service | CLS-payout-001 | `src/hotstreak_core/features/payout/` |
| API | CLS-payout-002 | `src/hotstreak_sync/api/payout/` |
| UI | CLS-payout-010 | `src/hotstreak_display/screens/payout.py` |
| UI | CLS-payout-011 | Phone Web（技術未確定） |
