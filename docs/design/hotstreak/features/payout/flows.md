# フロー: 配当

## シーケンス

```mermaid
sequenceDiagram
  participant Sync as Sync_server
  participant Display as Display_Pi
  participant Phone as Phone_Web
  participant Enter as RaspberryPi_Enter

  Note over Sync: race.finished → payout
  Sync->>Sync: settleRace
  Sync-->>Display: WS payout.state
  Sync-->>Phone: WS payout.state
  Enter->>Display: Enter
  Display->>Sync: POST advance API-PAYOUT-002
  alt raceIndex 1or2
    Sync->>Sync: resetBetweenRaces
    Sync-->>Display: WS payout.advanced phase=betting
    Sync-->>Phone: WS payout.advanced
  else raceIndex 3
    Sync-->>Display: WS payout.advanced phase=lobby
    Sync-->>Phone: WS payout.advanced
  end
```

## 状態遷移

| 状態 | イベント | 次の状態 |
|------|----------|----------|
| settling | race.finished | showing |
| showing | Enter (n<3) | between_reset → betting |
| showing | Enter (n=3) | lobby |

フェーズ: `payout` → `betting` または `lobby`。
