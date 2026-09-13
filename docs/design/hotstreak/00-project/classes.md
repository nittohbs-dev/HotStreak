# 共通クラス

プロジェクト横断のクラス。spec-browser では共通ノード（ティール）になる。

## クラス一覧

| CLS-ID | 名前 | 層 | 責務 | 関連TBL |
|--------|------|-----|------|---------|
| CLS-HS-001 | GameSession | Domain | セッション ID・フェーズ・参加者集合 | |
| CLS-HS-002 | Player | Domain | playerId・表示名・所持金・nameReady・手札 | |
| CLS-HS-003 | PhaseGate | Domain | 全員揃い / Enter による進行判定 | |
| CLS-HS-004 | RaceCard | Domain | レースカード1枚の識別・マスコット・効果ラベル | |
| CLS-HS-005 | CardSupply | Domain | 供給山からの公開・手札抽選（重複なし） | |
