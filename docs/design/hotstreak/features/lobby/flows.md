# フロー: 参加・ロビー

## シーケンス

```mermaid
sequenceDiagram
  participant Display as Display_Pi
  participant Sync as Sync_server
  participant Phone as Phone_Web
  participant Enter as RaspberryPi_Enter

  Display->>Sync: POST /api/sessions API-LOBBY-001
  Sync-->>Display: sessionId joinUrl
  Display->>Display: QR表示 SCR-display-001
  Phone->>Sync: POST join API-LOBBY-003
  Sync-->>Phone: playerId players
  Sync-->>Display: WS lobby.state
  Phone->>Sync: PUT name API-LOBBY-004
  Sync-->>Phone: WS lobby.state
  Sync-->>Display: WS lobby.state
  alt 全員名前確定
    Sync->>Sync: PhaseGate 全員揃い
    Sync-->>Phone: WS lobby.advanced
    Sync-->>Display: WS lobby.advanced
  else Enter押下
    Enter->>Display: Enter入力
    Display->>Sync: POST advance API-LOBBY-005
    Sync->>Sync: プレースホルダ名付与
    Sync-->>Phone: WS lobby.advanced
    Sync-->>Display: WS lobby.advanced
  end
```

## 状態遷移

| 状態 | イベント | 次の状態 |
|------|----------|----------|
| waiting_join | 1人目 join | name_pending |
| name_pending | 名前確定（一部） | name_pending |
| name_pending | 全員 nameReady | all_ready |
| all_ready | 自動または Enter | advanced |
| name_pending | Enter（3人以上） | advanced |
| advanced | — | setup-cards（別機能） |

フェーズ（GameSession.phase）: `lobby` → `setup-cards`。
