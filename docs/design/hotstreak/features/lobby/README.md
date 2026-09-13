# 参加・ロビー

## 概要

QR 参加とプレイヤー名の確定により、試合セッションへ参加者を集める。全端末で参加者一覧を同期し、初期所持金 $10 を付与する。セットアップ完了は **全員の名前確定** または **ラズパイ Enter** で次フェーズ（公開カード準備）へ進む。

## スコープ

| 含む | 含まない |
|------|----------|
| QR 参加・名前確定・参加者同期 | 公開カード・マ券（setup-cards / betting） |
| 初期所持金 $10 の付与 | 永続化・再参加・観戦者モード |
| 全員揃い / ラズパイ Enter で次フェーズ | タイマーによる画面遷移 |
| 参加者 3〜8 人 | 2人・9人以上バリアント |

## 関連一覧

| 種別 | ID | 名前 |
|------|-----|------|
| 画面 | SCR-phone-001 | ロビー（参加） |
| 画面 | SCR-display-001 | 参加受付 |
| API | API-LOBBY-001 | セッション作成 |
| API | API-LOBBY-002 | ロビー状態取得 |
| API | API-LOBBY-003 | 参加 |
| API | API-LOBBY-004 | 名前確定 |
| API | API-LOBBY-005 | フェーズ進行（Enter） |
| CLS | CLS-HS-001 | GameSession |
| CLS | CLS-HS-002 | Player |
| CLS | CLS-HS-003 | PhaseGate |
| CLS | CLS-lobby-001 | LobbyService |
| CLS | CLS-lobby-002 | LobbyApiHandler |
| CLS | CLS-lobby-010 | DisplayLobbyScreen |
| CLS | CLS-lobby-011 | PhoneLobbyScreen |
| DB | — | 永続化なし（対局中メモリ） |

## 依存機能

- なし（実装順の先頭機能）

## 受け入れ条件

- [ ] REQ-lobby-001: Display 起動時にセッションと参加用 QR が生成される
- [ ] REQ-lobby-002: Phone が QR 経由で参加し playerId を得る
- [ ] REQ-lobby-003: 名前確定で全端末の参加者一覧が同期更新される
- [ ] REQ-lobby-004: 名前確定時に初期所持金 $10 が付与される
- [ ] REQ-lobby-005: 参加者は 3〜8 人の範囲で維持される
- [ ] REQ-lobby-006: 全員名前確定または Enter で setup-cards に遷移する
- [ ] REQ-lobby-007: Enter 時の未確定プレイヤーはプレースホルダ名で確定される
- [ ] REQ-lobby-008: フェーズ遷移後は新規参加を受け付けない
