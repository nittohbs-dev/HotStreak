# 表記・規約

## 設計書

- 形の正本は `.agents/skills/design-doc`
- 表ヘッダ・ID 接頭辞を変えない
- 変更時はスキル・テンプレ・indexer を同時更新

## 本ツール固有

- キャンバスは読み取り専用。ノード追加・辺編集なし
- ソース全文を snapshot に埋め込まない（パスと ID ヒットのみ）
- Vite `base` は Pages で `/HotStreak/`、ローカルは `/`
