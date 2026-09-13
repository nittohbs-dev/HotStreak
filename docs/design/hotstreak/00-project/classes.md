# 共通クラス

プロジェクト横断のクラス。spec-browser では共通ノード（ティール）になる。

## クラス一覧

| CLS-ID | 名前 | 層 | 責務 | 関連TBL |
|--------|------|-----|------|---------|
| CLS-HS-001 | GameSession | Domain | セッション ID・フェーズ・参加者集合 | |
| CLS-HS-002 | Player | Domain | playerId・表示名・所持金・nameReady・手札・所持札 | |
| CLS-HS-003 | PhaseGate | Domain | 全員揃い / Enter による進行判定 | |
| CLS-HS-004 | RaceCard | Domain | レースカード1枚の識別・マスコット・効果ラベル | |
| CLS-HS-005 | CardSupply | Domain | 供給山からの公開・手札抽選（重複なし） | |
| CLS-HS-006 | BetTicket | Domain | マ券／サイドベット札の種類・表裏・ダブル指定 | |
| CLS-HS-007 | SideBetPrompt | Domain | サイドベットお題文面 | |
| CLS-HS-008 | SnakeDraft | Domain | スネーク手番・周回 | |
| CLS-HS-009 | RacingDeck | Domain | 公開＋仕込みによるレーシングデッキ | |
| CLS-HS-010 | Mascot | Domain | マスコット位置・向き・転倒・DQ | |
| CLS-HS-011 | Course | Domain | コースマス・短縮 | |
| CLS-HS-012 | RaceEngine | Domain | めくり・効果・終了判定 | |
