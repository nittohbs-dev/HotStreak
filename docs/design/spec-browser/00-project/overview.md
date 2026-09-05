# Spec Browser（設計把握ビューア）

## 目的

HotStreak 本体とは独立して、`docs/design/` とソースを読み、機能設計 → 共通クラス → DB の関係を Flowise 風のノードキャンバスで見せる。ビルド時に索引を固め、GitHub Pages でも開ける静的サイトにする。

## スコープ

| 含む | 含まない |
|------|----------|
| 設計 Markdown / manifest の索引 | ゲーム本体のプレイヤーUI |
| ソース上の追跡ID照合 | ノードを繋いで設計を書くエディタ |
| React Flow キャンバスと右インスペクタ | 右パネルのチャット / LLM |
| GitHub Pages への静的公開 | 公開サイトでのライブ再索引 |

## 用語集

| 用語 | 説明 |
|------|------|
| snapshot | ビルド時に生成する `snapshot.json`。nodes / edges / 詳細 |
| CLS- | クラス追跡ID。共通は `00-project/classes.md` |
| TBL- | テーブル追跡ID |
| 辺 | 機能→クラス、クラス→テーブル。設計表に書いたものだけ |
