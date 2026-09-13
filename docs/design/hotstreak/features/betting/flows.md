# フロー: マ券・サイドベット

## シーケンス

```mermaid
sequenceDiagram
  participant Sync as Sync_server
  participant Display as Display_Pi
  participant Phone as Phone_Web
  participant Enter as RaspberryPi_Enter

  Note over Sync: setup.advanced で phase=betting
  Sync->>Sync: BettingService.onEnterBetting
  Sync-->>Display: WS betting.state
  Sync-->>Phone: WS betting.state
  loop 各手番
    Phone->>Sync: POST picks API-BETTING-002
    Sync-->>Phone: WS betting.state
    Sync-->>Display: WS betting.state
  end
  opt 第3レース
    Phone->>Sync: PUT double API-BETTING-003
    Sync-->>Phone: WS betting.state
  end
  alt 全員2枚取得
    Sync->>Sync: PhaseGate 全員揃い
    Sync-->>Phone: WS betting.advanced
    Sync-->>Display: WS betting.advanced
  else Enter
    Enter->>Display: Enter
    Display->>Sync: POST advance API-BETTING-004
    alt 全員揃い
      Sync-->>Phone: WS betting.advanced
      Sync-->>Display: WS betting.advanced
    else 未完了
      Sync-->>Display: 409（force-advance なし）
    end
  end
```

## 状態遷移

| 状態 | イベント | 次の状態 |
|------|----------|----------|
| entering | setup.advanced | drafting |
| drafting | pick（未完了） | drafting |
| drafting | 全員2枚（＋第3ダブル） | all_ready |
| all_ready | 自動または Enter | advanced |
| drafting | Enter（未完了） | 409（force-advance なし） |
| advanced | — | card-seed |

フェーズ: `betting` → `card-seed`。
