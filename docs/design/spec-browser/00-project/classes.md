# 共通クラス

プロジェクト横断のクラス。spec-browser では共通ノード（ティール）になる。

## クラス一覧

| CLS-ID | 名前 | 層 | 責務 | 関連TBL |
|--------|------|-----|------|---------|
| CLS-sb-001 | DesignIndexer | Domain | 設計書スキーマに沿って nodes/edges/詳細を組み立てる | |
| CLS-sb-002 | SourceScanner | Domain | ソース木を走査し追跡ID・クラス名・テーブル名を照合する | |
| CLS-sb-003 | SnapshotModel | Domain | snapshot.json の形を保持する | |
