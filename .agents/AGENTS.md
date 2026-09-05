# HotStreak — ルール・スキル台帳

正本。ルート `AGENTS.md` は約50行の前提のみ。詳細はここに書く。
ユーザーがルールを直したら確認なしで本ファイル（または溢れ先）を更新する。

## 運用メモ

- 各節の目安は約50行。超えたら `.agents/rules/<topic>.md` へ抽出し、ここにはリンクと1行要約だけ残す
- スキル本体は `.agents/skills/<name>/SKILL.md`。ここには目次のみ
- 空の規則ファイルは作らない。必要になったら追加する

## ルール

### 開発フロー（SE / PG）

拘束の正本: [rules/dev-flow.md](rules/dev-flow.md)（設計書正本・ブランチ・Issue・`develop` 直編集禁止）。手順はスキル `dev-flow`。

### 設計書の形

正本はスキル `design-doc`（表ヘッダ・ID・章順）。形式変更はスキル・テンプレ・spec-browser indexer を同時に揃える。

### コミットメッセージ

- 本文は日本語で書く
- 先頭に種別を入れる。形式は `種別: 内容`
- 使う種別:
  - `add` — 新規追加
  - `fix` — 不具合や誤りの修正
  - `update` — 既存の更新
  - `docs` — 文書のみ
  - `chore` — 設定・雑務
- 例: `add: アセット用ディレクトリを追加する`

## スキル目次

| 名前 | いつ使うか | パス |
|------|------------|------|
| `dev-flow` | 設計・Issue・実装・PR・ブランチ・SE/PG・次何する | [skills/dev-flow/SKILL.md](skills/dev-flow/SKILL.md) |
| `design-doc` | 設計書の作成・更新・scaffold・スキーマ固定 | [skills/design-doc/SKILL.md](skills/design-doc/SKILL.md) |
