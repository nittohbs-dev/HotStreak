# 層設計: レース進行

## 責務マトリクス

| 層 | CLS-ID | 責務 | 関連API |
|----|--------|------|---------|
| Domain | CLS-HS-001 | フェーズ | API-RACE-001 |
| Domain | CLS-HS-009 | 山・バーン・めくり | RaceEngine |
| Domain | CLS-HS-010 | マスコット位置・状態 | race.state |
| Domain | CLS-HS-011 | コースマス・短縮 | race.state |
| Domain | CLS-HS-012 | 効果解決・終了判定 | race.finished |
| Service | CLS-race-001 | レースループ・配信 | API-RACE-001, 002 |
| API | CLS-race-002 | REST / WS | API-RACE-001, 002 |
| UI | CLS-race-010 | Display 演出 | API-RACE-001, 002 |
| UI | CLS-race-011 | Phone 観戦 | API-RACE-001 |

## 主要メソッド

| 層 | メソッド | やること |
|----|----------|----------|
| Service | startRace | シャッフル・バーン・GO |
| Service | resolveNextCard | 1枚めくり・効果適用 |
| Service | shortenCourse | 山切れ時の短縮 |
| Service | finishRace | 着順確定・payout へ |
| Domain | applyEffect | 英語ルールに従い effectKind を解決（設計書は要約のみ） |

## Python パッケージ配置（実装時）

| 層 | CLS-ID | 配置先 |
|----|--------|--------|
| Domain | CLS-HS-010〜012 | `src/hotstreak_core/domain/` |
| Service | CLS-race-001 | `src/hotstreak_core/features/race/` |
| API | CLS-race-002 | `src/hotstreak_sync/api/race/` |
| UI | CLS-race-010 | `src/hotstreak_display/screens/race.py` |
| UI | CLS-race-011 | Phone Web（技術未確定） |
