---
name: dev-flow
description: Enforces HotStreak SE/PG development flow with develop as integration branch, design-then-issue-then-implement order, and design docs as source of truth. Use when designing, implementing, creating issues or PRs, managing branches, or when the user asks 次何する, SE, PG, or workflow status.
---

# 開発フロー（SE / PG）

拘束の要約は [../../rules/dev-flow.md](../../rules/dev-flow.md)。本スキルは手順の正本。使えるスキルは `.agents/skills/` のみ。

## 開始時チェック（毎回）

1. `git branch --show-current` を実行する。
2. `develop` または `main` なら **ファイル操作をしない**。作業ブランチへ移ってから続ける。
3. 役割を決める。設計・設計PR・Issue 作成 → SE。Issue 番号付きの実装・実装PR → PG。曖昧なら確認する。

## フェーズ一覧

| Phase | 条件 | 役割 | ブランチ |
|-------|------|------|----------|
| 0 | `docs/design/` が無い／新規機能の設計開始 | SE | `design/<feature-id>` |
| 1 | 設計書作成中〜設計PR | SE | `design/<feature-id>` |
| 2 | 設計PRが `develop` に合併済み、Issue 未作成 | SE | （Issue 作成のみ。コード変更なし） |
| 3 | 実装 Issue あり | PG | `feat/<feature-id>-<req-id>` |
| 4 | 実装完了〜実装PR・レビュー | PG | 同 feat ブランチ |

推測で飛ばさない。合併前に Issue や実装へ進まない。

---

## Phase 0 / 1 — 設計（SE）

### やること

1. `develop` から `design/<feature-id>` を切る（既存ならチェックアウト）。
2. 設計書の作成・更新はスキル **`design-doc`** に従う（テンプレ・表ヘッダ・ID 固定）。外部スキルは使わない。
3. `docs/design/` に設計書を書く・更新する。実装コードは触らない。
4. コミットは台帳どおり。例: `docs: <feature-id> の設計を追加する`
5. ユーザーが設計を承認したら、base **`develop`** の設計PRを作る。
6. `main` 向けには出さない。

### 設計PR本文（最低限）

```markdown
## 概要
<機能の要約>

## 設計書
- パス: `docs/design/...`

## 確認依頼
- [ ] 要件と受け入れ条件
- [ ] API / 画面 / フロー（該当するもの）
```

### 禁止

- 設計ブランチでのアプリ実装
- `develop` 上での設計ファイル編集
- ユーザー未承認での設計PR強行（承認を確認する）

---

## Phase 2 — Issue 作成（SE）

### 前提

- 設計PRが **`develop` に合併済み** であること。未合併なら停止する。

### やること

1. Epic Issue を1つ作る（機能単位）。
2. 要件（REQ-ID）ごとに Sub-Issue を作る。
3. 各 Sub-Issue に設計書パス・REQ-ID・受け入れ条件へのリンクを書く。
4. Epic から Sub-Issue を一覧で参照できるようにする。
5. Issue URL をユーザーに報告する。

### Sub-Issue 本文（最低限）

```markdown
## 要件
- REQ-ID: <id>
- 機能: <feature-id>

## 設計書
- <docs/design へのパス>

## 受け入れ条件
- [ ] <設計書から転記>

## 実装ルール
- 設計書を正本とする（リードオンリー）
- ブランチ: `feat/<feature-id>-<req-id>`
- PR base: `develop`
```

### 禁止

- 合併前の Issue 作成
- Issue 作成と同時の実装開始

---

## Phase 3 — 実装（PG）

### 前提

- 実装対象の **Issue 番号** があること。無ければ SE フェーズへ戻すよう報告して停止する。

### やること

1. Issue から REQ-ID・feature-id・設計書パス・受け入れ条件を読む。
2. `develop` から `feat/<feature-id>-<req-id>` を切る（REQ が1つだけの機能なら `feat/<feature-id>` 可）。
3. Issue が指す設計書だけを根拠に実装する。`docs/design/` は原則編集しない。
4. 軽微な仕様調整は **ユーザーが明示したときだけ**、同じ feat PR 内で設計書も直す。REQ 追加・API パス変更などは別の設計PRが必要と報告して止める。
5. コミットは台帳どおり。例: `add: REQ-xxx のログインAPIを実装する`。本文またはメッセージに REQ-ID / feature-id を含める。

### 禁止

- Issue なし実装
- 設計に無い機能の独断追加
- `develop` / `main` 上での編集

---

## Phase 4 — 実装PR（PG）

### やること

1. base **`develop`** で実装PRを開く（`main` 禁止）。
2. Issue が指す設計書とブランチ上の実装を突き合わせる。
3. **設計書との差分** を PR 本文に必ず書く。
   - 差分がある → 箇所を列挙し、理由をその feat ブランチの **コミット履歴**（`git log` / `git show` のメッセージと差分）から読む。推測で理由を作らない。
   - 履歴に理由が無い → コミットメッセージを直すか、PR に「理由がコミット履歴から読み取れない」と明記する。
   - 差分が無い → 「設計書との差分なし」と書く。
4. レビュー指摘への対応も同じ feat ブランチで行う。
5. E2E や追加テストが必要なら、設計書のテスト章と Issue 範囲に従って同じフローで進める（別スキルへ逃がさない。詳細手順が肥大化したら `.agents/skills/` に新スキルを足す）。

### 実装PR本文テンプレート

```markdown
## 概要
- Issue: #<n>
- REQ-ID: <id>
- 設計書: `docs/design/...`

## 変更内容
- <実装の要点>

## 設計書との差分
- なし
  または
- <箇所>: <どう違うか>
  - 理由（コミット履歴より）: <hash / メッセージから要約>
```

### 禁止

- 設計と違う実装を差分節なしで出す
- 理由を履歴を見ずに作文する
- base を `main` にする

---

## 次に何をするか（短く判断）

1. 現在ブランチと、設計PR / Issue / 実装PR の有無を見る。
2. 上表の Phase に当てはめる。
3. 該当 Phase の手順だけを実行する。飛ばさない。

報告例: `いま Phase 2（設計は develop 合併済み、Issue 未作成）。次は Epic と REQ Issue を作る。`
