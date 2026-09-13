# レース進行

## 概要

レーシングデッキをシャッフルし、3枚バーン（「3, 2, 1…GO!」）の後に1枚ずつめくってカード効果を解決する。山切れでリシャッフル＋コース短縮。マスコット3体がゴールまたは失格したら着順を確定し payout へ。プレイヤー操作によるフェーズ遷移はなく、**ルール演算**で進む。

## スコープ

| 含む | 含まない |
|------|----------|
| バーン・めくり・効果解決・DQ・コース短縮 | マ券取得・仕込み |
| Display レース演出・Phone 観戦要約 | 配当計算（payout） |
| 着順確定の配信 | タイマーによる遷移 |
| サイドベットお題の継続表示 | カード効果の原作全文転載 |

## 関連一覧

| 種別 | ID | 名前 |
|------|-----|------|
| 画面 | SCR-phone-004 | レース観戦 |
| 画面 | SCR-phone-004b | 全員状況（小画面） |
| 画面 | SCR-display-005 | レース進行 |
| API | API-RACE-001 | レース状態取得 |
| API | API-RACE-002 | （任意）観戦購読のみ。進行はサーバ主導 |
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

- [ ] REQ-race-001: 開始時に3枚バーンし GO 演出後にめくりを開始する
- [ ] REQ-race-002: めくったカードの効果をマスコット位置に反映する
- [ ] REQ-race-003: 山切れでリシャッフル＋コース短縮を行う
- [ ] REQ-race-004: 3体ゴールまたは失格で着順確定し payout へ遷移する
- [ ] REQ-race-005: Phone に自分のマ券・所持金・順位要約を表示する
- [ ] REQ-race-006: 全員状況小画面で他プレイヤーの札を参照できる

## 根拠で閉じた項目

| 旧ID | 決定 | 根拠 |
|------|------|------|
| OPEN-race-001 | 設計書には効果の**種別名＋要約のみ**。詳細解決の正は英語ルールブック。全文転載しない。要約は `manual.html` §6 をデジタル説明の正とする | [`overview.md`](../../00-project/overview.md) スコープ外「ルール全文の転載」、同「英語ルールブックを構造の正」、[`manual.html`](../../manual.html) §6 効果表 |
| OPEN-race-003 | DQ は manual 要約どおり: 転倒中の再転倒／衝突、コース外、短縮で埋まる、など | `manual.html` §6「失格（DQ）」行 |
| OPEN-race-004 | コース短縮は**奥が消える／左から折りたたみ**（次の solid white line まで）。埋まった位置のマスコットは失格。山切れのたびに発生しうる | [rulebook](https://gamers-hq.de/media/pdf/dc/37/cf/Hot_Streak_rulebook_2nd_printing.pdf) RESHUFFLING「fold it over to the next solid white line… stragglers under the mat are disqualified」。display/screens.md |
| OPEN-race-005 | 進行は**サーバ主導の自動進行**。Display 演出完了 ack（API-RACE-002）は設けない | `display/screens.md` SCR-display-005「（なし）\| 自動進行」 |
| OPEN-race-006 | レース中に起きた事実を race 終了時に確定し、`race.finished` で sideBetOutcome 等を載せ **payout が精算**する | overview フロー race→payout、`manual.html` §6（事象）→§⑥配当 |
| OPEN-race-002 | **デジタル正本: 4レーン × START〜GOAL 間 12マス**。★マーカーはスタートから 3・6・9 列目。ワイヤー上のコース短縮は 3マス単位（12の1/4） | 数え方: [`ゲーム進行画面-ディスプレイ側.png`](../../../wireframes/display/ゲーム進行画面-ディスプレイ側.png) 画面1・4で START〜GOAL の緑マス列を列挙（12列）。物理盤は Misut Meeple が「14 rows × 4 lanes」と記述（https://misutmeeple.com/en/2026/02/review-hot-streak/）— **物理14との差分あり。本デジタル設計はワイヤー12を採用** |

## OPEN（確認待ち）

（コースマス長は上記どおり閉じた。物理14との要否は実装前の確認事項として下記「推奨／注記」に残す）

### 注記（物理との差分）

物理マットを 14 行とする二次資料あり。デジタルワイヤーは 12。公式 PDF に数値なし。物理準拠に切り替える場合は Course モデルを差し替える。

