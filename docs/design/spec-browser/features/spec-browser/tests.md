# テスト設計: 設計把握キャンバス

## トレーサビリティ

| TST-ID | 種別 | 対象 | 観点 | 関連REQ | 関連SCR/CMP | Playwright spec |
|--------|------|------|------|---------|-------------|-----------------|
| TST-sb-001 | E2E | 空状態 | プレースホルダ表示 | REQ-sb-002 | SCR-sb-002 | tools/spec-browser/tests/e2e/TST-sb-001.spec.ts |
| TST-sb-002 | E2E | キャンバス | ノードと辺の表示 | REQ-sb-002 | SCR-sb-001 | tools/spec-browser/tests/e2e/TST-sb-002.spec.ts |
| TST-sb-003 | E2E | インスペクタ | 選択で詳細更新 | REQ-sb-003 | SCR-sb-001 | tools/spec-browser/tests/e2e/TST-sb-003.spec.ts |

種別: **E2E** = Playwright E2E、`CT` = Playwright Component Test

## E2E シナリオ

| TST-ID | 画面 | 操作 | 期待結果 |
|--------|------|------|----------|
| TST-sb-001 | SCR-sb-002 | 空 snapshot で開く | 案内ノードが見える |
| TST-sb-002 | SCR-sb-001 | サンプル snapshot で開く | Feature/Class/Table と辺が見える |
| TST-sb-003 | SCR-sb-001 | 機能ノードをクリック | 右パネルに REQ が出る |

## コンポーネントシナリオ

| CMP-ID | TST-ID | 観点 | 期待結果 |
|--------|--------|------|----------|
| | | | |

## バックエンド（JUnit — Playwright 対象外）

| TST-ID | 層 | 観点 | 関連REQ |
|--------|-----|------|---------|
| TST-sb-010 | Indexer | テンプレ表だけから辺を作る | REQ-sb-001 |
| TST-sb-011 | Scanner | 除外パスを走査しない | REQ-sb-005 |

## 受け入れ条件マッピング

| REQ-ID | カバーする TST-ID |
|--------|-------------------|
| REQ-sb-001 | TST-sb-010 |
| REQ-sb-002 | TST-sb-001, TST-sb-002 |
| REQ-sb-003 | TST-sb-003 |
| REQ-sb-004 | （CI 手動確認） |
| REQ-sb-005 | TST-sb-011 |
