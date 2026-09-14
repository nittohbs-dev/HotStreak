# 層設計: 設計把握キャンバス

## 責務マトリクス

| 層 | CLS-ID | 責務 | 関連API |
|----|--------|------|---------|
| Domain | CLS-sb-001 | 設計書をパースし nodes/edges を作る（全 project・継承辺・Api 辺含む） | |
| Domain | CLS-sb-002 | ソース走査と ID 照合 | |
| Domain | CLS-sb-003 | snapshot の形を定義・検証 | |
| UI | CLS-sb-010 | キャンバス画面の組み立てとフィルタ状態 | |
| UI | CLS-sb-011 | 機能ノード表示 | |
| UI | CLS-sb-012 | クラスノード表示（共通/固有） | |
| UI | CLS-sb-013 | テーブルノード表示 | |
| UI | CLS-sb-014 | インスペクタ（関連ジャンプ） | |
| UI | CLS-sb-015 | アウトライン（機能マルチ選択・エンドポイント節） | |
| UI | CLS-sb-016 | プロジェクト切替 | |
| UI | CLS-sb-017 | モバイル・ドロワーシェル | |
| UI | CLS-sb-018 | Api（エンドポイント）ノード表示 | |

## 主要メソッド

| 層 | メソッド | やること |
|----|----------|----------|
| Domain | indexDesign | テンプレ表だけを読みグラフを構築（projectId 接頭辞・Api ノード・関連API 辺） |
| Domain | scanSources | 除外パス以外を走査しヒットを付与 |
| Domain | writeSnapshot | public/snapshot.json を書く |
| UI | selectProject | 表示スコープを1プロジェクトに限定 |
| UI | selectFeatures | 機能マルチ選択で部分グラフを出す |
| UI | selectNode | 選択とクエリ同期、関連ハイライト |
| UI | openMobileDrawer | 一覧/詳細の排他オープン |
| UI | relayoutVisible | 表示中ノードを Feature / Class(層) / Api / Table で詰め直して fitView |
| UI | toggleOutlineSection | アウトラインの層/エンドポイント/TBL セクション開閉 |

## メソッド: CLS-sb-001

| メソッド | 引数 | 戻り値 | 概要 |
|----------|------|--------|------|
| indexDesign | `{ designRoot }` | `{ projects[], nodes[], edges[], details }` | 全 manifest を読みグラフを組み立てる |
| parseApiBodies | `{ apiMd }` | `{ apiId, requestJson?, responseJson? }[]` | API 節の JSON を抽出する |
| parseRelatedApis | `{ relatedApiCell }` | `API-…[]` | 関連API セルから ID を抽出する |

## メソッド: CLS-sb-010

| メソッド | 引数 | 戻り値 | 概要 |
|----------|------|--------|------|
| relayoutVisible | `{ visibleNodeIds }` | （副作用: ノード座標更新） | 表示中だけ層サブ列込みで詰め直して fitView |
