# Spec Browser（設計把握ビューア）

## 目的

HotStreak 本体とは独立して、`docs/design/` とソースを読み、機能設計 → 共通クラス → DB の関係を Flowise 風のノードキャンバスとアウトラインで見せる。ビルド時に索引を固め、GitHub Pages でも開ける静的サイトにする。

## スコープ

| 含む | 含まない |
|------|----------|
| 設計 Markdown / manifest の索引（任意の `<projectId>`） | ゲーム本体のプレイヤーUI |
| ソース上の追跡ID照合 | ノードを繋いで設計を書くエディタ |
| React Flow キャンバス・アウトライン・インスペクタ | 右パネルのチャット / LLM |
| プロジェクト切替・機能マルチ選択・検索・ギャップのみ | Wiki / リポジトリ全体の MD ビューア（次フェーズ） |
| デスクトップ三ペインとモバイル（≤768px）ドロワー | ネイティブアプリ / PWA 必須化 |
| 任意列「継承元」による Class→Class 破線辺 | 公開サイトでのライブ再索引 |
| GitHub Pages への静的公開 | |

## 用語集

| 用語 | 説明 |
|------|------|
| snapshot | ビルド時に生成する `snapshot.json`。projects / nodes / edges / 詳細 |
| 設計プロジェクト | `docs/design/<projectId>/manifest.yaml` がある単位。表示は常に1件 |
| CLS- | クラス追跡ID。共通は `00-project/classes.md` |
| TBL- | テーブル追跡ID |
| 継承元 | クラス表の任意列。値は `CLS-…`。辺 `inherits` の正本 |
| 辺 | 機能→クラス、クラス→テーブル、クラス→クラス（継承）。設計表に書いたものだけ |
