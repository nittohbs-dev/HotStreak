---
version: alpha
name: HotStreak Display UI
description: 会場ディスプレイ（Pygame 1280×720）のビジュアル基準。画面フロー・REQ は features/*/screens.md と wireframes/display/screens.md。
colors:
  roomShadow: "#090c11"
  roomFloor: "#2e1f1d"
  headerBg: "#090c11"
  headerBorder: "#cabe9f"
  panelBg: "#0c0f14"
  panelBorder: "#7c6343"
  textPrimary: "#ebe9e0"
  textGold: "#dfbf86"
  textMuted: "#c8b890"
  textError: "#f49780"
  cardFrame: "#ad9063"
  cardInner: "#0d141c"
  cardAccent: "#dac396"
  mascotGobbler: "#e77d4d"
  mascotHurley: "#5eb2e1"
  mascotDangle: "#e2bd55"
  mascotMum: "#a5b975"
  lampWarm: "#f39336"
typography:
  displayLg:
    fontFamily: "Yu Gothic UI, Meiryo, Noto Sans CJK JP, IPAGothic, sans-serif"
    fontSize: 44px
    fontWeight: 700
    lineHeight: 1.1
  displayMd:
    fontFamily: "{typography.displayLg.fontFamily}"
    fontSize: 32px
    fontWeight: 700
    lineHeight: 1.15
  displaySm:
    fontFamily: "{typography.displayLg.fontFamily}"
    fontSize: 24px
    fontWeight: 700
    lineHeight: 1.2
  body:
    fontFamily: "{typography.displayLg.fontFamily}"
    fontSize: 20px
    fontWeight: 700
    lineHeight: 1.25
  caption:
    fontFamily: "{typography.displayLg.fontFamily}"
    fontSize: 16px
    fontWeight: 700
    lineHeight: 1.3
rounded:
  card: 0px
spacing:
  safe: 20px
  headerH: 65px
  footerH: 51px
  cardGap: 18px
components:
  topBar:
    backgroundColor: "{colors.headerBg}"
    textColor: "{colors.textPrimary}"
    height: "{spacing.headerH}"
  footerBar:
    backgroundColor: "{colors.roomShadow}"
    textColor: "{colors.textGold}"
    height: "{spacing.footerH}"
  infoStrip:
    backgroundColor: "{colors.panelBg}"
    textColor: "{colors.textPrimary}"
    padding: "12px 24px"
  faceUpCard:
    backgroundColor: "{colors.cardInner}"
    textColor: "{colors.textPrimary}"
    rounded: "{rounded.card}"
    padding: "9px"
  brandMark:
    textColor: "{colors.textMuted}"
    typography: "{typography.caption}"
---

# HotStreak — Display visual system

## Overview

会場ディスプレイは **1280×720 固定**の横画面。暗い「部屋」背景に、吊りランプの暖色と **金茶の枠**でカード・UI を載せる（実装参考: `src/hotstreak_display/screens/setup_cards.py`）。ピクセル風の床・マスコットはレトロゲーム寄りだが、UI テキストは太めゴシックで遠くから読めること優先。

PNG ストーリーボード（[試合開始前設計.png](./試合開始前設計.png)、[ゲーム進行画面](./ゲーム進行画面-ディスプレイ側.png)）は構図の参考。色・字は本トークンと実装が優先。

## Colors

| 役割 | トークン | 用途 |
|------|----------|------|
| 背景 | `roomShadow` / `roomFloor` | 部屋・床のドット絵 |
| ヘッダー | `headerBg` + `headerBorder` | 画面上帯・2px 枠 |
| パネル | `panelBg` + `panelBorder` | 説明帯・フッター枠 |
| 本文 | `textPrimary` | 日本語メイン |
| 強調 | `textGold` | 人数・枚数・Enter 案内 |
| 補助 | `textMuted` | HOT STREAK ロゴ等 |
| エラー | `textError` | 接続・状態エラー |
| カード | `cardFrame` / `cardInner` / `cardAccent` | 公開カードの額縁 |
| マスコット | `mascot*` 4色 | Gobbler / Hurley / Dangle / Mum |
| 照明 | `lampWarm` | 天井ランプのグロー（背景のみ） |

マスコット色はカード隅の飾り・ピクセルアイコンと **同じ4色**に揃える。

## Typography

- すべて **太字ゴシック**（Pygame 実装では 16〜44px を用途で使い分け）。
- 会場最前列から読む想定で、本文でも `body`（20px）未満にしない。
- 英字ロゴ `HOT STREAK` は `caption` サイズ・`textMuted`。

## Layout

- **キャンバス**: 1280×720。安全余白 `safe`（20px）。
- **上帯**: 高さ `headerH`。左に画面タイトル、右にブランド。
- **中央**: コンテンツ（公開カードは最大2行×5列、枚数多いときはコンパクト行）。
- **下帯**: 高さ `footerH`。Enter 案内・エラー・進行状態を1行で表示。
- レース画面（未実装）も同じ上帯＋下帯＋中央舞台の三層を維持する。

## Elevation & Depth

奥行きは **背景のパース床**とランプのグローで表現。UI パネルはフラット＋2px 枠。カードは右下に 6px オフセットの影色矩形（`(6,8,13)`）で「置いてある」感だけ付ける。

## Shapes

- カード・パネルは **直角**（`rounded.card: 0`）。ボードゲームの実カードに近い。
- マスコットはピクセルグリッド（ドット絵）。滑らかなベクターイラストに置き換えない（将来アセット化する場合も同じシルエット）。

## Components

| 部品 | 見え方 | 備考 |
|------|--------|------|
| `topBar` | 暗背景＋金枠 | 全画面共通 |
| `infoStrip` | 中央の説明テキスト帯 | 公開カード枚数など |
| `faceUpCard` | 金枠・暗面・マスコット | `effectLabel` は2行まで |
| `footerBar` | Enter 文言・エラー | `textGold` / `textError` |
| `brandMark` | 右上 HOT STREAK | 操作説明は載せない |

## Do's and Don'ts

**Do**

- プレイヤー操作 UI は載せない（操作はスマホ）。会場向け **共有情報と演出**のみ。
- コース短縮演出は「左から畳む」イメージ（ワイヤー「崩壊」ではなく短縮）。
- 日本語フォント未導入環境では起動失敗させ、システムフォントに黙ってフォールバックしない（実装方針）。

**Don't**

- スマホの白面・青アクセント UI をディスプレイに流用しない。
- 本ファイルに SCR 一覧・API・画面遷移を書かない。
- フェーズ進行のカウントダウンタイマー UI（旧ワイヤーの秒数表示）を復活させない。
