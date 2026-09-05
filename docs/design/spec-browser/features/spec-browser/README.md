# 設計把握キャンバス

## 概要

`docs/design/` とソースをビルド時に索引し、機能 → クラス → DB をノードキャンバスで表示する。右インスペクタで詳細を見せ、GitHub Pages に静的公開する。

## スコープ

| 含む | 含まない |
|------|----------|
| indexer / snapshot / キャンバス / インスペクタ / Pages | 設計エディタ、チャット、ライブ再索引 |

## 関連一覧

| 種別 | ID | 名前 |
|------|-----|------|
| 画面 | SCR-sb-001 | キャンバス本体 |
| 画面 | SCR-sb-002 | 空状態キャンバス |
| CLS | CLS-sb-001 | DesignIndexer |
| CLS | CLS-sb-002 | SourceScanner |
| CLS | CLS-sb-003 | SnapshotModel |
| CLS | CLS-sb-010 | CanvasApp |
| CLS | CLS-sb-011 | FeatureNode |
| CLS | CLS-sb-012 | ClassNode |
| CLS | CLS-sb-013 | TableNode |
| CLS | CLS-sb-014 | InspectorPanel |

## 依存機能

- なし（設計書スキーマは `.agents/skills/design-doc`）

## 受け入れ条件

- [ ] REQ-sb-001: テンプレ表だけから snapshot が生成される
- [ ] REQ-sb-002: 機能→クラス→テーブルが左から右のノードで見える
- [ ] REQ-sb-003: ノード選択で右インスペクタが更新される
- [ ] REQ-sb-004: `develop` 合併で Pages に静的ビルドが載る
- [ ] REQ-sb-005: ソース照合バッジとギャップ件数が表示される
