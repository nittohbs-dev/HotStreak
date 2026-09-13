# 層設計: 公開カード準備

## 責務マトリクス

| 層 | CLS-ID | 責務 | 関連API |
|----|--------|------|---------|
| Domain | CLS-HS-001 | フェーズ・参加者数の保持 | API-SETUP-001 |
| Domain | CLS-HS-002 | 手札3枚の保持 | （自動配布） |
| Domain | CLS-HS-003 | Enter による進行判定 | API-SETUP-002 |
| Domain | CLS-HS-004 | レースカード1枚の識別・マスコット・効果ラベル | API-SETUP-001 |
| Domain | CLS-HS-005 | 供給山からの公開・手札抽選（重複なし） | （自動配布） |
| Service | CLS-setup-001 | 入場時配布・公開状態・advance | API-SETUP-001, 002 |
| API | CLS-setup-002 | REST / WebSocket ハンドラ・配信 | API-SETUP-001, 002 |
| UI | CLS-setup-010 | Display: 公開カードグリッド／レーン描画・Enter 連携 | API-SETUP-001, 002 |

## 主要メソッド

| 層 | メソッド | やること |
|----|----------|----------|
| Service | onEnterSetupCards | スターター＋追加公開＋手札3枚を配布し setup.state を配信 |
| Service | getSetupState | 公開カードと dealt フラグを返す |
| Service | advanceSetup | 配布完了を確認しフェーズを betting に |
| Domain | drawFaceUp | 人数表に従い公開カードを取り出す |
| Domain | dealHands | 各 Player に3枚配る |
| UI | renderFaceUpGrid | Display に公開カードを描画 |

## Python パッケージ配置（実装時）

| 層 | CLS-ID | 配置先 |
|----|--------|--------|
| Domain | CLS-HS-004, 005 | `src/hotstreak_core/domain/` |
| Service | CLS-setup-001 | `src/hotstreak_core/features/setup_cards/` |
| API | CLS-setup-002 | `src/hotstreak_sync/api/setup_cards/` |
| UI | CLS-setup-010 | `src/hotstreak_display/screens/setup_cards.py` |
