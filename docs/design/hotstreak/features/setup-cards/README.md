# 公開カード準備

## 概要

ロビー完了後、スターター4枚（マスコット各1）と人数分のランダム公開カードを表向きに並べ、各プレイヤーへ初期手札3枚を配る。Display で公開カードとレーン気配を共有し、**ラズパイ Enter** で次フェーズ（マ券ドラフト）へ進む。Phone 専用画面は持たない。

## スコープ

| 含む | 含まない |
|------|----------|
| 公開カードの抽選・表向き公開・レーン表示 | マ券・サイドベット（betting） |
| 初期手札3枚の配布 | カード仕込み・デッキ組成の最終確定（card-seed） |
| Enter による betting への遷移 | タイマーによる画面遷移 |
| 参加人数 3〜8 人に応じた公開枚数 | 2人・9人以上バリアント |

## 関連一覧

| 種別 | ID | 名前 |
|------|-----|------|
| 画面 | SCR-display-002 | 公開カード |
| API | API-SETUP-001 | 公開カード状態取得 |
| API | API-SETUP-002 | フェーズ進行（Enter） |
| CLS | CLS-HS-001 | GameSession |
| CLS | CLS-HS-002 | Player |
| CLS | CLS-HS-003 | PhaseGate |
| CLS | CLS-HS-004 | RaceCard |
| CLS | CLS-HS-005 | CardSupply |
| CLS | CLS-setup-001 | SetupCardsService |
| CLS | CLS-setup-002 | SetupCardsApiHandler |
| CLS | CLS-setup-010 | DisplaySetupCardsScreen |
| DB | — | 永続化なし（対局中メモリ） |

## 依存機能

- 先行: [lobby](../lobby/)（フェーズ `lobby` → `setup-cards`、参加者確定・所持金）

## 受け入れ条件

- [ ] REQ-setup-001: setup-cards 入場時に公開カードと初期手札が自動配布される
- [ ] REQ-setup-002: スターターはマスコット各1枚（計4）を含む
- [ ] REQ-setup-003: 追加公開枚数は人数表どおり（3人:11 … 8人:6）
- [ ] REQ-setup-004: 各プレイヤーの手札は3枚
- [ ] REQ-setup-005: Display に公開カードが同期表示される
- [ ] REQ-setup-006: Enter で betting へ遷移する
- [ ] REQ-setup-007: 公開＋後続の仕込み枚数で開始時山が18枚になる前提を満たす

## 暫定採用（レビュー確認依頼）

ユーザー明示回答前に設計を前進させるため、本ドラフトの解釈を **採用** する（PR 確認チェックリストで覆せる）。

| 項目 | 採用内容 |
|------|----------|
| 公開枚数 | 総公開＝スターター4＋追加ランダム（人数表）。overview「3人:11…」は追加枚数 |
| Phone | 専用画面なし。待機のみ。`setup.advanced` 後に betting |
| 遷移 | Enter（advance）のみで `betting` へ。タイマー／全員揃いなし |
