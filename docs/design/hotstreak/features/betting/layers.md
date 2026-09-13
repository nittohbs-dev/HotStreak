# 層設計: マ券・サイドベット

## 責務マトリクス

| 層 | CLS-ID | 責務 | 関連API |
|----|--------|------|---------|
| Domain | CLS-HS-001 | フェーズ・raceIndex | API-BETTING-001 |
| Domain | CLS-HS-002 | 所持札・ダブル指定の保持 | API-BETTING-002, 003 |
| Domain | CLS-HS-003 | 全員揃い / Enter 判定 | API-BETTING-004 |
| Domain | CLS-HS-006 | マ券／サイドベット札の種類・表裏 | API-BETTING-002 |
| Domain | CLS-HS-007 | サイドベットお題文面 | API-BETTING-001 |
| Domain | CLS-HS-008 | スネーク手番・周回 | API-BETTING-002 |
| Service | CLS-betting-001 | 入場・pick・double・advance | API-BETTING-001〜004 |
| API | CLS-betting-002 | REST / WebSocket | API-BETTING-001〜004 |
| UI | CLS-betting-010 | Display 共有画面 | API-BETTING-001, 004 |
| UI | CLS-betting-011 | Phone ドラフト画面 | API-BETTING-001〜003 |

## 主要メソッド

| 層 | メソッド | やること |
|----|----------|----------|
| Service | onEnterBetting | お題提示・在庫初期化・先頭手番設定 |
| Service | pickTicket | 在庫確認・表裏確定・次手番 |
| Service | setDouble | 第3の1枚ダブル指定 |
| Service | advanceBetting | 全員揃い／Enter で card-seed へ |
| Domain | nextTurn | スネーク順の次プレイヤー |

## Python パッケージ配置（実装時）

| 層 | CLS-ID | 配置先 |
|----|--------|--------|
| Domain | CLS-HS-006〜008 | `src/hotstreak_core/domain/` |
| Service | CLS-betting-001 | `src/hotstreak_core/features/betting/` |
| API | CLS-betting-002 | `src/hotstreak_sync/api/betting/` |
| UI | CLS-betting-010 | `src/hotstreak_display/screens/betting.py` |
| UI | CLS-betting-011 | Phone Web クライアント（技術未確定） |

Enter 未完了は advance=409・force-advance なし（採用）。先頭は Display 指定（公式 unluckiest）。
