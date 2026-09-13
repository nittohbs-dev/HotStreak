# 層設計: 参加・ロビー

## 責務マトリクス

| 層 | CLS-ID | 責務 | 関連API |
|----|--------|------|---------|
| Domain | CLS-HS-001 | セッション ID・フェーズ・参加者集合 | API-LOBBY-002 |
| Domain | CLS-HS-002 | playerId・表示名・所持金・nameReady | API-LOBBY-003, 004 |
| Domain | CLS-HS-003 | 全員揃い / Enter による進行判定 | API-LOBBY-005 |
| Service | CLS-lobby-001 | 参加・名前確定・advance のユースケース | API-LOBBY-003, 004, 005 |
| API | CLS-lobby-002 | REST / WebSocket ハンドラ・配信 | API-LOBBY-001〜005 |
| UI | CLS-lobby-010 | Display: QR・参加者一覧・Enter 連携 | API-LOBBY-001, 002, 005 |
| UI | CLS-lobby-011 | Phone: 名前入力・一覧・確定 | API-LOBBY-003, 004 |

## 主要メソッド

| 層 | メソッド | やること |
|----|----------|----------|
| Service | createSession | 新規 GameSession を生成し joinUrl を返す |
| Service | joinSession | playerId を発行し参加者に追加 |
| Service | confirmName | 表示名を確定し $10 付与・nameReady を true |
| Service | advanceLobby | プレースホルダ名付与・全員揃い判定・フェーズを setup-cards に |
| API | broadcastLobbyState | 接続クライアントへ lobby.state を送る |
| UI | renderQrAndRoster | Display に QR と参加者リストを描画 |
| UI | submitPlayerName | Phone で名前確定 API を呼ぶ |

## Python パッケージ配置（実装時）

| 層 | CLS-ID | 配置先 |
|----|--------|--------|
| Domain | CLS-HS-001〜003 | `src/hotstreak_core/domain/` |
| Service | CLS-lobby-001 | `src/hotstreak_core/features/lobby/` |
| API | CLS-lobby-002 | `src/hotstreak_sync/api/lobby/` |
| UI | CLS-lobby-010 | `src/hotstreak_display/screens/lobby.py` |
| UI | CLS-lobby-011 | Phone Web クライアント（技術未確定） |
