---
version: alpha
name: HotStreak Phone UI
description: スマホ操作画面のビジュアル基準（google-labs design.md 形式）。画面フロー・REQ は features/*/screens.md と wireframes/phone/screens.md。
colors:
  ink: "#1a1a1a"
  muted: "#6f6f6b"
  line: "#d6d6d2"
  paper: "#ffffff"
  fill: "#f4f4f2"
  accent: "#2f6fb0"
  accentBg: "#e8f0f8"
  success: "#2e6b45"
  successBg: "#e7f1ea"
  risk: "#9a4a2f"
  riskBg: "#f7ebe5"
  highlight: "#f6efe2"
  canvas: "#e9e9e5"
typography:
  body:
    fontFamily: "Hiragino Kaku Gothic ProN, Noto Sans JP, Yu Gothic, system-ui, sans-serif"
    fontSize: 14px
    fontWeight: 400
    lineHeight: 1.6
  title:
    fontFamily: "{typography.body.fontFamily}"
    fontSize: 20px
    fontWeight: 600
    lineHeight: 1.3
  section:
    fontFamily: "{typography.body.fontFamily}"
    fontSize: 16px
    fontWeight: 600
    lineHeight: 1.35
  caption:
    fontFamily: "{typography.body.fontFamily}"
    fontSize: 12px
    fontWeight: 400
    lineHeight: 1.5
  label:
    fontFamily: "{typography.body.fontFamily}"
    fontSize: 11px
    fontWeight: 400
    lineHeight: 1.4
rounded:
  sm: 4px
  md: 8px
  lg: 10px
  phone: 14px
spacing:
  xs: 6px
  sm: 10px
  md: 14px
  lg: 18px
  phonePadding: 18px
components:
  phoneShell:
    backgroundColor: "{colors.paper}"
    textColor: "{colors.ink}"
    rounded: "{rounded.phone}"
    padding: "{spacing.phonePadding}"
  panel:
    backgroundColor: "{colors.fill}"
    rounded: "{rounded.md}"
    padding: 14px
  row:
    backgroundColor: "{colors.paper}"
    textColor: "{colors.ink}"
    rounded: "{rounded.md}"
    padding: "10px 12px"
  rowSelected:
    backgroundColor: "{colors.paper}"
    textColor: "{colors.ink}"
    rounded: "{rounded.md}"
    padding: "9px 11px"
  primaryButton:
    backgroundColor: "{colors.paper}"
    textColor: "{colors.ink}"
    rounded: "{rounded.md}"
    padding: 11px
  accentBar:
    backgroundColor: "{colors.accentBg}"
    textColor: "{colors.accent}"
    rounded: "{rounded.md}"
    padding: "9px 11px"
  moneyBlock:
    backgroundColor: "{colors.successBg}"
    textColor: "{colors.success}"
    rounded: "{rounded.md}"
    padding: 13px
  tagSafe:
    backgroundColor: "{colors.fill}"
    textColor: "{colors.muted}"
    rounded: 6px
    padding: "5px 11px"
  tagRisky:
    backgroundColor: "{colors.riskBg}"
    textColor: "{colors.risk}"
    rounded: 6px
    padding: "5px 11px"
  sideBetEvent:
    backgroundColor: "{colors.highlight}"
    rounded: "{rounded.md}"
    padding: 11px
---

# HotStreak — Phone visual system

## Overview

スマホは **明るい紙面 UI**（会場の暗いディスプレイと対になる）。プレイヤーが片手で操作する前提で、コントラストは読みやすさ優先。見た目の参考実装は [hotstreak-wireframes.html](./hotstreak-wireframes.html)。画面の役割・遷移・API は設計書（`docs/design/hotstreak/features/*/screens.md`）を正本とし、本ファイルは **色・字・余白・部品の見え方だけ** を固定する。

トーン: 落ち着いた卓上ゲーム向けのユーティリティ UI。派手なグラデーションやダークモード全面は使わない。

## Colors

| 役割 | トークン | 用途 |
|------|----------|------|
| 本文 | `ink` | 見出し・本文・主ボタン枠 |
| 補助 | `muted` | 説明・ラベル・スタンプ |
| 区切り | `line` | 枠線・区切り線 |
| 面 | `paper` | 画面カード・入力背景 |
| 薄い面 | `fill` | パネル・タグ（セーフ） |
| 操作強調 | `accent` / `accentBg` | 手番バー・選択枠・リンク風テキスト |
| 所持金・成功 | `success` / `successBg` | 配当・所持金ブロック |
| リスキー | `risk` / `riskBg` | リスキー札・ダブル指定 |
| お題 | `highlight` | サイドベットお題・リードセル |
| 一覧背景 | `canvas` | ワイヤー一覧の外周（本番アプリは通常 `paper` 全面） |

セーフ／リスキーは **色で意味を分ける**（`tagSafe` / `tagRisky`）。リスキーは茶系、セーフはグレー面。

## Typography

- 日本語ゴシック系のみ。欧文は同スタックにフォールバック。
- 画面タイトル `title`、セクション `section`、本文 `body`、補足 `caption`、ラベル `label` の5段階で足りる。それ以上のサイズ階層は増やさない。
- 金額の強調は `moneyBlock` 内で大きめ（ワイヤーでは 24px 相当）— トークン外の例外はこのブロックだけ。

## Layout

- **想定幅**: モバイル 360〜390px 相当。ワイヤーは 340px の「電話枠」で検証している。
- **余白**: 画面内 `phonePadding`、ブロック間 `md`、行間 `xs`。
- **リスト**: `row` を縦積み。選択中は 2px の `accent` 枠（`rowSelected`）。
- **手札・カード**: 3列グリッド（`gap: 8px`）。選択カードは `accent` 枠 2px。
- **下部固定**: 主操作は `primaryButton` を画面下寄せ（ワイヤー `margin-top: 14px`）。

## Elevation & Depth

フラット中心。影は使わず、**1px の `line` 枠**と背景色の差で階層を出す。モーダル（全員状況）は背面を暗くする程度で、ドロップシャドウは任意・控えめ。

## Shapes

- 角丸は `md`（8px）を標準。電話外枠のみ `phone`（14px）。
- アバターは正円（30px）。チップ・バッジは `sm`（4px）。

## Components

| 部品 | 見え方 | 状態 |
|------|--------|------|
| `phoneShell` | 白面・細枠 | — |
| `panel` | 灰面のまとまり | — |
| `row` / `rowSelected` | リスト行 | 選択で accent 枠 |
| `primaryButton` | 白地・黒枠・全幅 | 押下は opacity のみで可 |
| `accentBar` | 手番・進行案内 | — |
| `moneyBlock` | 緑系の配当強調 | — |
| `sideBetEvent` | お題用の温かいベージュ面 | — |
| `tagSafe` / `tagRisky` | マ券の裏表ラベル | 文言は **セーフ／リスキー** |

## Do's and Don'ts

**Do**

- ラベルは規約どおり **マ券**（馬券表記は使わない）。
- フェーズ案内は「全員揃い／Enter」文言。カウントダウン UI は置かない。
- タップ領域は行・ボタンとも縦 44px 以上を目安にする。

**Don't**

- 紫グラデ・汎用 SaaS 風パレット（本トークン外の色を増やさない）。
- ディスプレイ用の暗い部屋ビジュアルをスマホ全面に流用しない。
- 画面仕様（SCR・API・遷移）を本ファイルに書かない — それは `screens.md` / 機能設計の役割。
