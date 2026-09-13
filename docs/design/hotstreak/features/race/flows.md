# フロー: レース進行

## シーケンス

```mermaid
sequenceDiagram
  participant Sync as Sync_server
  participant Display as Display_Pi
  participant Phone as Phone_Web

  Note over Sync: seed.advanced → race
  Sync->>Sync: startRace バーン
  Sync-->>Display: WS race.state fx=burn
  Sync-->>Phone: WS race.state
  loop めくり
    Sync->>Sync: resolveNextCard
    Sync-->>Display: WS race.state
    Sync-->>Phone: WS race.state
    opt 山切れ
      Sync->>Sync: shortenCourse
      Sync-->>Display: WS race.state fx=shorten
    end
  end
  Sync->>Sync: finishRace
  Sync-->>Display: WS race.finished
  Sync-->>Phone: WS race.finished
```

## 状態遷移

| 状態 | イベント | 次の状態 |
|------|----------|----------|
| starting | burn+GO | resolving |
| resolving | card resolved | resolving |
| resolving | deck empty | shortening |
| shortening | done | resolving |
| resolving | 3 finished | finished |
| finished | — | payout |

フェーズ: `race` → `payout`。
