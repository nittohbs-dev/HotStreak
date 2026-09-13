# フロー: 公開カード準備

## シーケンス

```mermaid
sequenceDiagram
  participant Sync as Sync_server
  participant Display as Display_Pi
  participant Phone as Phone_Web
  participant Enter as RaspberryPi_Enter

  Note over Sync: lobby.advanced で phase=setup-cards
  Sync->>Sync: SetupCardsService.onEnterSetupCards
  Sync-->>Display: WS setup.state
  Sync-->>Phone: WS setup.state
  Display->>Display: SCR-display-002 描画
  Phone->>Phone: 待機表示
  Enter->>Display: Enter入力
  Display->>Sync: POST advance API-SETUP-002
  Sync->>Sync: phase=betting
  Sync-->>Display: WS setup.advanced
  Sync-->>Phone: WS setup.advanced
```

## 状態遷移

| 状態 | イベント | 次の状態 |
|------|----------|----------|
| entering | lobby.advanced | dealing |
| dealing | 配布成功 | face_up_ready |
| dealing | 供給不足 | failed（セッション再作成） |
| face_up_ready | Enter | advanced |
| advanced | — | betting（別機能） |

フェーズ（GameSession.phase）: `setup-cards` → `betting`。
