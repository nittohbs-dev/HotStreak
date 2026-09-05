# 層設計: 設計把握キャンバス

## 責務マトリクス

| 層 | CLS-ID | 責務 | 関連API |
|----|--------|------|---------|
| Domain | CLS-sb-001 | 設計書をパースし nodes/edges を作る | |
| Domain | CLS-sb-002 | ソース走査と ID 照合 | |
| Domain | CLS-sb-003 | snapshot の形を定義・検証 | |
| UI | CLS-sb-010 | キャンバス画面の組み立て | |
| UI | CLS-sb-011 | 機能ノード表示 | |
| UI | CLS-sb-012 | クラスノード表示（共通/固有） | |
| UI | CLS-sb-013 | テーブルノード表示 | |
| UI | CLS-sb-014 | 右インスペクタ | |

## 主要メソッド

| 層 | メソッド | やること |
|----|----------|----------|
| Domain | indexDesign | テンプレ表だけを読みグラフを構築 |
| Domain | scanSources | 除外パス以外を走査しヒットを付与 |
| Domain | writeSnapshot | public/snapshot.json を書く |
| UI | selectNode | 選択とクエリ同期、関連ハイライト |
