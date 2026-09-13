# 設計把握キャンバス

## 概要

`docs/design/` とソースをビルド時に索引し、任意の設計プロジェクトを1件ずつ、機能 → クラス → DB をノードキャンバスとアウトラインで表示する。インスペクタで詳細を見せ、GitHub Pages に静的公開する。モバイルはキャンバス主面＋ドロワー。

## スコープ

| 含む | 含まない |
|------|----------|
| indexer / snapshot / キャンバス / アウトライン / インスペクタ / プロジェクト切替 / 機能マルチ選択 / 検索 / 継承辺 / モバイル / Pages | 設計エディタ、チャット、ライブ再索引、Wiki |

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
| CLS | CLS-sb-015 | OutlinePanel |
| CLS | CLS-sb-016 | ProjectSwitcher |
| CLS | CLS-sb-017 | MobileShell |

## 依存機能

- なし（設計書スキーマは `.agents/skills/design-doc`）

## 受け入れ条件

- [ ] REQ-sb-001: テンプレ表だけから snapshot が生成され、ID に projectId 接頭辞が付く
- [ ] REQ-sb-002: 機能→クラス→テーブルが左から右のノードで見え、継承は破線
- [ ] REQ-sb-003: ノード選択でインスペクタが更新され、関連クリックで遷移する
- [ ] REQ-sb-004: `develop` 合併で Pages に静的ビルドが載る
- [ ] REQ-sb-005: ソース照合バッジとギャップ件数（選択プロジェクト分）が表示される
- [ ] REQ-sb-006: 任意の設計プロジェクトを切り替えられ、他プロジェクトは混在しない
- [ ] REQ-sb-007: 左アウトラインで機能→クラス→TBL を辿れる
- [ ] REQ-sb-008: 機能を複数チェックすると共有クラスを含む部分グラフが見える
- [ ] REQ-sb-009: 検索とギャップのみで絞り込める
- [ ] REQ-sb-010: `継承元` を書いたクラスだけ破線辺が出る
- [ ] REQ-sb-011: ≤768px でキャンバス主面＋排他ドロワーが使える
