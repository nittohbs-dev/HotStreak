# フロー: カード仕込み

## シーケンス

```mermaid
sequenceDiagram
  participant Sync as Sync_server
  participant Display as Display_Pi
  participant Phone as Phone_Web
  participant Enter as RaspberryPi_Enter

  Note over Sync: betting.advanced → card-seed
  Sync-->>Display: WS seed.state
  Sync-->>Phone: WS seed.state
  loop 各プレイヤー
    Phone->>Sync: POST seed API-SEED-002
    Sync-->>Phone: WS seed.state
    Sync-->>Display: WS seed.state
  end
  alt 全員仕込み
    Sync->>Sync: buildRacingDeck
    Sync-->>Phone: WS seed.advanced
    Sync-->>Display: WS seed.advanced
  else Enter
    Enter->>Display: Enter
    Display->>Sync: POST advance API-SEED-003
    alt 全員 seeded
      Sync-->>Phone: WS seed.advanced
      Sync-->>Display: WS seed.advanced
    else 未仕込み
      Sync-->>Display: 409（force-advance なし）
    end
  end
```

## 状態遷移

| 状態 | イベント | 次の状態 |
|------|----------|----------|
| seeding | seed（一部） | seeding |
| seeding | 全員 seeded | deck_ready |
| deck_ready | 自動または Enter | advanced |
| seeding | Enter（未仕込み） | 409（force-advance なし） |
| advanced | — | race |

フェーズ: `card-seed` → `race`。
