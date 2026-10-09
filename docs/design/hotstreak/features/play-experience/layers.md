# 層設計: 会場プレイ体験

| 層 | CLS-ID | 責務 | 関連API |
|----|--------|------|---------|
| Domain | CLS-play-001 | GameSession: 先着者・進行条件・総合優勝の状態遷移。Room: 排他と配信 | API-play-001 |
| UI | CLS-play-002 | 会場とPhoneの総合優勝、進行ボタン、全画面設定 | API-play-001 |
| UI | CLS-play-003 | 看板・線・カード・名前の描画 | — |
| UI | CLS-audio-001 | 5秒間隔の音声点検と状態表示 | — |
| Infrastructure | CLS-audio-002 | 再生停止・デバイス障害からの復旧 | — |
