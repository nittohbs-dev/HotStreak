# アーキテクチャ

## 技術スタック

| 層 | 技術 |
|----|------|
| UI | React + TypeScript + Vite + `@xyflow/react` |
| 索引 | Node スクリプト（ビルド前） |
| 公開 | GitHub Pages（静的 `dist`） |
| 入力 | `docs/design/`、`frontend/` / `backend/` / `src/`（読み取り専用） |

## システム構成

```mermaid
flowchart LR
  designDocs["docs/design"]
  sourceTree["frontend / backend / src"]
  indexer["indexer at build"]
  snapshot["snapshot.json"]
  staticSite["Vite dist"]
  pages["GitHub Pages"]
  designDocs --> indexer
  sourceTree --> indexer
  indexer --> snapshot
  snapshot --> staticSite
  staticSite --> pages
```

## 配置

| パス | 役割 |
|------|------|
| `tools/spec-browser/` | ビューア本体 |
| `docs/design/<projectId>/` | 入力。`manifest.yaml` があるディレクトリはすべて設計プロジェクト（名前非依存） |
| `.github/workflows/spec-browser-pages.yml` | `develop` 合併後に Pages 公開 |

## マルチプロジェクト

indexer は `docs/design/` 直下の全 `manifest.yaml` を1つの `snapshot.json` に載せる。UI は `?project=` で常に1プロジェクトだけ表示する（混在させない）。
