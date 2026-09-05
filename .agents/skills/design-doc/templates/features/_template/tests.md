# テスト設計: <機能名>

## トレーサビリティ

| TST-ID | 種別 | 対象 | 観点 | 関連REQ | 関連SCR/CMP | Playwright spec |
|--------|------|------|------|---------|-------------|-----------------|
| TST-xxx-001 | E2E | 画面フロー | 正常系 | REQ-xxx-001 | SCR-xxx-001 | tests/e2e/TST-xxx-001.spec.ts |
| TST-xxx-002 | CT | コンポーネント | バリデーション | REQ-xxx-002 | CMP-xxx-001 | tests/components/CMP-xxx-001.spec.ts |

種別: **E2E** = Playwright E2E、`CT` = Playwright Component Test

## E2E シナリオ

| TST-ID | 画面 | 操作 | 期待結果 |
|--------|------|------|----------|
| TST-xxx-001 | SCR-xxx-001 | | |

## コンポーネントシナリオ

| CMP-ID | TST-ID | 観点 | 期待結果 |
|--------|--------|------|----------|
| CMP-xxx-001 | TST-xxx-002 | | |

## バックエンド（JUnit — Playwright 対象外）

| TST-ID | 層 | 観点 | 関連REQ |
|--------|-----|------|---------|
| | Service | | |
| | Controller | | |

## 受け入れ条件マッピング

| REQ-ID | カバーする TST-ID |
|--------|-------------------|
| REQ-xxx-001 | TST-xxx-001, ... |
