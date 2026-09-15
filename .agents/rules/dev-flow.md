# 開発フロー拘束（SE / PG）

AI が勝手な判断で崩さないための固定ルール。手順の詳細は `.agents/skills/dev-flow/SKILL.md`。

## スキルの正本

- **使えるスキルは `.agents/skills/` のみ。**
- プラグイン、`.cursor/skills`、`~/.cursor/skills` は読まない・使わない・リンクしない。
- 足りない手順は `.agents/skills/` に足す。外部スキルへ誘導しない。

## 正本は設計書

- 実装の根拠は Issue が指す `docs/design/`。
- 設計書の形の正本はスキル `design-doc`（テンプレ・表ヘッダ・ID）。
- コードが先で設計が後追い、は原則禁止。
- 実装中の `docs/design/` はリードオンリー。軽微な仕様調整はユーザー明示時のみ、同じ feat PR 内。

## 役割

| 役割 | やること | やってはいけないこと |
|------|----------|----------------------|
| SE | 設計書、`design/*`、設計PR、`develop` 合併後の Issue 作成 | 実装コード、`feat/*` |
| PG | 開いている実装 Issue（REQ-ID）と参照設計書に基づく実装・実装PR | Issue なし実装、自由ブランチ、設計の独断変更 |

役割が曖昧なら、設計作業か Issue 番号かを確認してから動く。推測でブランチを切らない。

## ブランチ

| 用途 | 名前 | PR base |
|------|------|---------|
| 統合 | `develop` | —（直編集禁止） |
| 設計（SE） | `design/<feature-id>` | `develop` |
| 実装（PG） | `feat/<feature-id>-<req-id>`（REQ が1つだけなら `feat/<feature-id>` 可） | `develop` |

- **`develop` / `main` 上ではファイルの作成・編集・削除を一切しない。** 作業前に `git branch --show-current` を確認する。該当なら即停止し、作業ブランチへ移ってから触る。コミットもステージも禁止。更新は PR 合併だけ。
- 1 機能 1 設計PR。1 Issue 1 実装ブランチ 1 実装PR。
- `main` への PR・マージ・直コミットは禁止（リリースはユーザー明示の別作業）。

### 許可しないブランチ・操作

- `feature/`、日付名、人名ブランチ
- `main` / `develop` 直コミット
- `main` 向け PR
- 設計ブランチでの実装
- 実装ブランチでの設計新規作成

## Issue

- 設計PRが **`develop` に合併されたあと** だけ Epic 1 + REQ ごと Sub-Issue を作る。
- 合併前の Issue 作成・実装開始は拒否する。
- PG は Issue 番号なしでは実装を始めない。無い場合は SE フェーズへ戻す。

## GitHub — PR と Issue の紐付け

| PR 種別 | Issue との関係 |
|---------|----------------|
| 設計PR（SE） | この時点では Issue 未作成。**キーワードで Issue を閉じない。** 本文に「Issue: 合併後に SE が Epic / Sub を作成」と書く。 |
| 実装PR（PG） | 対象の **Sub-Issue 1 件** を PR で閉じる。本文に `Closes #<sub-issue番号>`（または `Fixes #<同番号>`）を **必ず** 含める。Epic は `Issue: #<epic> / Sub: #<sub>` のように番号で参照する。 |

- PR 本文の `Issue:` 行と `Closes`/`Fixes` の番号は、作業中の Issue と一致させる。推測で番号を書かない。
- 1 実装PR = 1 Sub-Issue = 1 `Closes`（複数 Issue を1 PR で閉じない）。

## GitHub — レビュー依頼

- **設計PR・実装PR** を開いたら、レビュアー **`burokku-xp`**（プロジェクトオーナー）へのレビュー依頼を **必ず** 出す。
- PR 本文だけに「レビューお願いします」と書いて終わりにしない。GitHub 上で Reviewer としてリクエストする（`gh pr edit` / GitHub MCP 等）。
- オーナー以外を勝手にレビュアーに追加しない（明示指示があるときだけ）。

## develop の同期（ブランチを切る前）

- `design/*` / `feat/*` を **`develop` から切る直前** に、エージェントが **`git fetch origin develop`** を実行する（ユーザーに頼まなくてよい）。
- ローカル `develop` を基点にする場合: `git checkout develop` → `git pull origin develop`（または fetch 後に fast-forward できる状態にする）→ そこから `git checkout -b …`。
- **`develop` / `main` 上では編集しない** 拘束は変わらない。fetch / pull は同期のためだけ。
- スナップショット等でリモートより古い可能性があるときも、**毎回** ブランチ作成前に fetch する。

## 実装PR（必須）

- Issue が指す設計書と実装を突き合わせる。
- **差分・変更がある箇所は PR 本文に書く。** 理由は推測せず、その feat ブランチのコミット履歴（メッセージと差分）から読む。
- 履歴に理由が無い変更は、コミットを直すか「理由が分からない」と PR に明記する。
- 差分が無いなら「設計書との差分なし」と書く。黙って設計と違う実装を出さない。

## 逸脱時

上記に合わない依頼・状態なら作業を止め、どの拘束に抵触するかを短く報告する。代替の勝手なフローで進めない。
