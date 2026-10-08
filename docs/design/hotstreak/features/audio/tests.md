# テスト設計: 会場BGM・効果音

## トレーサビリティ

| TST-ID | 種別 | 対象 | 観点 | 関連REQ | 関連SCR/CMP | Playwright spec |
|--------|------|------|------|---------|-------------|-----------------|
| TST-audio-001 | pytest | 会場音声制御 | 同一通知・フレームの重複防止、待機間の曲継続、音量とループ | REQ-audio-001 | SCR-display-001〜006 | tests/hotstreak_display/test_audio.py |
| TST-audio-002 | pytest | 開始・カード演出 | 3・2・1・GOと画面同期、公開中の転倒・逆走の先走り防止、足音の頻度制限 | REQ-audio-001 | SCR-display-005 | tests/hotstreak_display/test_audio.py |
| TST-audio-003 | pytest | 着順・配当 | 最終演出待ち、goalのみゴール音、配当音1回、従来会場経路の即時結果も確認 | REQ-audio-001 | SCR-display-005, SCR-display-006 | tests/hotstreak_display/test_audio.py |
| TST-audio-004 | pytest | 再接続・セッション境界 | 3レースとロビー復帰、途中初回受信の過去音なし、別セッション識別 | REQ-audio-001 | SCR-display-001〜006 | tests/hotstreak_display/test_audio.py |
| TST-audio-005 | pytest | 音声障害・終了 | デバイスなし、一部素材欠落、BGM読込失敗、再生失敗でもゲーム継続、終了時停止 | REQ-audio-001 | — | tests/hotstreak_display/test_audio.py |
| TST-audio-006 | 実時間E2E | 実HTTP会場セッション | 待機から結果まで録画、8種の発音記録、録音の長さ・非無音・音割れ、画面・クレジット確認 | REQ-audio-001 | SCR-display-001〜006 / CMP-audio-001 | scripts/record-audio-preview.py |

## 受け入れ条件マッピング

| REQ-ID | カバーする TST-ID |
|--------|-------------------|
| REQ-audio-001 | TST-audio-001〜006 |

ラズパイの物理スピーカー確認は、このMac上の動作・録音検証とは別に扱う。画面のないテストはSDLのダミーデバイスで実行し、実時間E2Eは実デバイスと会場ウィンドウで実行する。
