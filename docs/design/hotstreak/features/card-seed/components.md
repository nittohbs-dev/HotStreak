# UIコンポーネント: カード仕込み

## コンポーネントツリー

```mermaid
flowchart TD
  subgraph display [Display SCR-display-004]
    DApp[CMP-seed-001 DisplaySeedRoot] --> DProg[CMP-seed-002 SeedProgress]
    DApp --> DDeck[CMP-seed-003 DeckBundlePreview]
  end
  subgraph phone [Phone SCR-phone-003]
    PApp[CMP-seed-010 PhoneSeedRoot] --> PHand[CMP-seed-011 HandPicker]
    PApp --> PStat[CMP-seed-012 SeedStatusList]
    PApp --> PBtn[CMP-seed-013 SeedConfirmButton]
  end
```

## コンポーネント一覧

| CMP-ID | 名前 | 役割 | 親 | 主な入出力 |
|--------|------|------|-----|------------|
| CMP-seed-001 | DisplaySeedRoot | Display 仕込み画面 | — | seed.state |
| CMP-seed-002 | SeedProgress | 進捗 n/人数 | CMP-seed-001 | progress |
| CMP-seed-003 | DeckBundlePreview | 束枚数プレビュー | CMP-seed-001 | deckCountExpected |
| CMP-seed-010 | PhoneSeedRoot | Phone 仕込み画面 | — | seed.state, hand |
| CMP-seed-011 | HandPicker | 手札選択 | CMP-seed-010 | handCardId |
| CMP-seed-012 | SeedStatusList | 全員の済／未 | CMP-seed-010 | progress |
| CMP-seed-013 | SeedConfirmButton | 仕込み確定 | CMP-seed-010 | → API-SEED-002 |
