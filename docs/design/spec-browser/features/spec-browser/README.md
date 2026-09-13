# 設計把握キャンバス

## 概要

`docs/design/` とソースをビルド時に索引し、任意の設計プロジェクトを1件ずつ、機能 → クラス → DB をノードキャンバスと層別アウトラインで表示する。絞り込み時はノードを詰め直す。インスペクタで概要・データ形（JSON/メソッド）を見せ、GitHub Pages に静的公開する。

## スコープ

| 含む | 含まない |
|------|----------|
| indexer / snapshot / キャンバス再配置 / 層別アウトライン / インスペクタ（JSON・メソッド） / プロジェクト切替 / 機能マルチ選択 / 検索 / 継承辺 / モバイル / Pages | 設計エディタ、チャット、ライブ再索引、Wiki |

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
- [ ] REQ-sb-002: 機能→クラス→テーブルが左から右のノードで見え、継承は破線。絞り込み後は再配置
- [ ] REQ-sb-003: ノード選択でインスペクタが更新され、関連クリックで遷移する。データ形を表示
- [ ] REQ-sb-004: `develop` 合併で Pages に静的ビルドが載る
- [ ] REQ-sb-005: ソース照合バッジとギャップ件数（選択プロジェクト分）が表示される
- [ ] REQ-sb-006: 任意の設計プロジェクトを切り替えられ、他プロジェクトは混在しない
- [ ] REQ-sb-007: アウトラインが機能＋層/API/TBL の折りたたみで辿れる
- [ ] REQ-sb-008: 機能を複数チェックすると共有クラスを含む部分グラフが見える
- [ ] REQ-sb-009: 検索とギャップのみで絞り込める
- [ ] REQ-sb-010: `継承元` を書いたクラスだけ破線辺が出る
- [ ] REQ-sb-011: ≤768px でキャンバス主面＋排他ドロワーが使える
- [ ] REQ-sb-012: 表示集合変化後にノードが詰まって再配置される
- [ ] REQ-sb-013: API JSON・クラスメソッド表がインスペクタに出る（未記載は許容）
