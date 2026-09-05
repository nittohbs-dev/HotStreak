---
name: design-doc
description: Creates HotStreak design documents under docs/design/ with fixed tables and IDs that the spec-browser indexer can read. Use when designing, drafting 設計書, scaffolding docs/design, or changing design schema.
---

# 設計書（design-doc）

使えるスキルは `.agents/skills/` のみ。プラグインの design-doc は使わない。

設計書の形は **spec-browser の読み取り契約**でもある。見出し・表ヘッダ・ID をテンプレから変えない。変えるときは本スキル・テンプレ・`tools/spec-browser` の indexer を同じ変更で揃える。

## 章順

1. 機能設計（`features/<id>/` の README / functional / screens / api）
2. クラス設計（共通: `00-project/classes.md`、機能: `layers.md` + `classes.md`）
3. DB（`00-project/db.md` 任意、機能: `db.md`）

## 開始時

1. `git branch --show-current` を確認。`develop` / `main` なら編集しない。
2. ブランチは `design/<feature-id>`（フローは `dev-flow`）。
3. `docs/design/<project>/` が無ければ [templates/](templates/) から scaffold する。

## Scaffold

```
docs/design/<project>/
├── manifest.yaml
├── 00-project/
│   ├── overview.md
│   ├── architecture.md
│   ├── feature-map.md
│   ├── conventions.md
│   ├── classes.md          # 共通 CLS-（必須。0件なら空表）
│   └── db.md               # 全体ER・共通 TBL-（任意）
└── features/<feature-id>/
    ├── README.md
    ├── functional.md
    ├── screens.md          # 画面があるとき
    ├── api.md              # API があるとき
    ├── layers.md           # 必須。CLS-ID 列
    ├── classes.md          # 必須。機能→CLS
    ├── db.md               # 永続化があるとき
    ├── components.md
    ├── flows.md
    └── tests.md
```

コピー元: 本スキルの `templates/`。プレースホルダを実名に置き換える。

## 固定 ID

| 接頭辞 | 用途 |
|--------|------|
| REQ- | 要件 |
| UC- | ユースケース |
| BR- | ビジネスルール |
| API- | API |
| SCR- | 画面 |
| CMP- | UIコンポーネント |
| TST- | テスト |
| CLS- | クラス |
| TBL- | テーブル |

クラス列に裸のクラス名だけは不可。必ず `CLS-`。

## indexer が読む表（ヘッダ一字固定）

| ファイル | 必須 | 表ヘッダ |
|----------|------|----------|
| `manifest.yaml` | 必須 | `project`, `title`, `status`, `features[].id` |
| `00-project/feature-map.md` | 必須 | `機能ID` / `名前` / `ステータス` / `概要` |
| `00-project/classes.md` | 必須 | `CLS-ID` / `名前` / `層` / `責務` / `関連TBL` |
| `00-project/db.md` | 任意 | 全体ER、共通 `TBL-` |
| `features/<id>/README.md` | 必須 | 関連一覧に 画面/API/CLS/TBL |
| `features/<id>/functional.md` | 必須 | UC / BR / `REQ-` 節 |
| `features/<id>/screens.md` | 画面あり | `SCR-ID` 一覧、遷移 Mermaid、ASCIIワイヤー |
| `features/<id>/api.md` | APIあり | `API-ID` / `メソッド` / `パス` / … |
| `features/<id>/layers.md` | 必須 | `層` / `CLS-ID` / `責務` / `関連API` |
| `features/<id>/classes.md` | 必須 | `CLS-ID` / `共通or固有` / `関連TBL` |
| `features/<id>/db.md` | 永続化あり | `テーブル: TBL-` とカラム表 |

## 辺（キャンバス）

indexer は推測で辺を増やさない。

- 機能 → クラス: その機能の `classes.md` / `layers.md` に出た CLS-
- クラス → テーブル: クラス表の「関連TBL」
- 共通クラス: `00-project/classes.md` 掲載

## 書いてよいこと / 書いてはいけないこと

**書く:** 要約表、Mermaid、追跡ID、責務の自然言語

**書かない:** クラスシグネチャ、DTO/Props の型定義、テンプレに無いファイル名・列、コードブロックでの実装詳細

## 完了後

1. `manifest.yaml` の features と feature-map を同期する。
2. ユーザーに draft レビューを依頼する（承認前に設計PRを強行しない。手順は `dev-flow`）。
3. 承認後の PR / Issue は `dev-flow` に従う。
