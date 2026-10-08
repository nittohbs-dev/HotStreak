# レース進行

## 概要

レーシングデッキをシャッフルし、3枚バーン（「3, 2, 1…GO!」）の後に1枚ずつめくってカード効果を解決する。山切れでリシャッフル＋コース短縮。マスコット3体がゴールまたは失格したら着順を確定し payout へ。プレイヤー操作によるフェーズ遷移はなく、**ルール演算**で進む。

## スコープ

| 含む | 含まない |
|------|----------|
| バーン・めくり・効果解決・DQ・コース短縮 | マ券取得・仕込み |
| Display レース演出・Phone 観戦要約 | 配当計算（payout） |
| 着順確定の配信・Enterによる自動進行の開始／停止 | タイマーによる着順確定 |
| サイドベットお題の継続表示 | カード効果の原作全文転載 |

## 関連一覧

| 種別 | ID | 名前 |
|------|-----|------|
| 画面 | SCR-phone-004 | レース観戦 |
| 画面 | SCR-phone-004b | 全員状況（小画面） |
| 画面 | SCR-display-005 | レース進行 |
| API | API-RACE-001 | レース状態取得 |
| API | API-RACE-002 | 既存advanceによる1枚進行要求 |
| CLS | CLS-HS-001 | GameSession |
| CLS | CLS-HS-002 | Player |
| CLS | CLS-HS-004 | RaceCard |
| CLS | CLS-HS-009 | RacingDeck |
| CLS | CLS-HS-010 | Mascot |
| CLS | CLS-HS-011 | Course |
| CLS | CLS-HS-012 | RaceEngine |
| CLS | CLS-race-001 | RaceService |
| CLS | CLS-race-002 | RaceApiHandler |
| CLS | CLS-race-010 | DisplayRaceScreen |
| CLS | CLS-race-011 | PhoneRaceScreen |
| DB | — | 永続化なし |

## 依存機能

- 先行: card-seed（`RacingDeck` 確定）
- 後続: payout

## 受け入れ条件

- [ ] REQ-race-001: 開始時に3枚バーンし GO 演出後にEnter待ちに入る
- [ ] REQ-race-002: めくったカードの効果をマスコット位置に反映する
- [ ] REQ-race-003: 山切れでリシャッフル＋コース短縮を行う
- [ ] REQ-race-004: 3体ゴールまたは失格で着順確定し payout へ遷移する
- [ ] REQ-race-005: Phone に自分のマ券・所持金・順位要約を表示する
- [ ] REQ-race-006: 全員状況小画面で他プレイヤーの札を参照できる

- [ ] REQ-race-008: Enterだけで自動進行の開始・停止・再開ができ、演出中の停止、短押しと1秒長押しの分岐・リピート抑止、終了・通信失敗時のOFFを満たす

## 根拠で閉じた項目

| 旧ID | 決定 | 根拠 |
|------|------|------|
| OPEN-race-001 | 設計書には効果の**種別名＋要約のみ**。詳細解決の正は英語ルールブック。全文転載しない。要約は `manual.html` §6 をデジタル説明の正とする | [`overview.md`](../../00-project/overview.md) スコープ外「ルール全文の転載」、同「英語ルールブックを構造の正」、[`manual.html`](../../manual.html) §6 効果表 |
| OPEN-race-003 | DQ は manual 要約どおり: 転倒中の再転倒／衝突、コース外、短縮で埋まる、など | `manual.html` §6「失格（DQ）」行 |
| OPEN-race-004 | コース短縮は**奥が消える／左から折りたたみ**（次の solid white line まで）。埋まった位置のマスコットは失格。山切れのたびに発生しうる | [rulebook](https://gamers-hq.de/media/pdf/dc/37/cf/Hot_Streak_rulebook_2nd_printing.pdf) RESHUFFLING「fold it over to the next solid white line… stragglers under the mat are disqualified」。display/screens.md |
| OPEN-race-005 | **Enter短押しで1枚、1秒長押しで自動開始、自動中の押下で停止**。演出完了後に次の1枚を要求し、効果解決はサーバ担当 | 2026-10-08ユーザー指示。従来の1押下1枚を置換 |
| OPEN-race-006 | レース中に起きた事実を race 終了時に確定し、`race.finished` で sideBetOutcome 等を載せ **payout が精算**する | overview フロー race→payout、`manual.html` §6（事象）→§⑥配当 |
| OPEN-race-002 | **デジタル正本: 4レーン × 13マス＋GOAL**。STARTは3マス目（列2）、★は3・8・13マス目（列2・7・12）、ゴール境界は13。コース短縮は3マス単位 | 2026-10-07ユーザー指定の並びに更新 |

## OPEN（確認待ち）

（コースマス長は上記のユーザー指定で確定）

### 注記（物理との差分）

デジタル盤面はユーザー指定の13マス＋GOALを正本とする。
