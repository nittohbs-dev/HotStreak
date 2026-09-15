# 規約

## 設計書

- 形の正本は `.agents/skills/design-doc`
- 表ヘッダ・ID 接頭辞を変えない
- ルール・流れの正本は [`overview.md`](./overview.md)（原作寄せ）。ワイヤーはラフ

## 用語表記

| 使う | 使わない（旧ワイヤー） |
|------|------------------------|
| マ券 | 馬券 |
| セーフ / リスキー | ノーマル（セーフの旧称として注記のみ可） |
| 今回のカード / サイドベット | イベント（曖昧） |
| 第3レースは1枚ダブル | 払戻すべて×2 |
| 全員揃い / ラズパイ Enter | 時間経過による画面遷移 |

## 進行トリガー

- フェーズ遷移にタイマーを使わない
- **全員揃い**または **ラズパイ Enter** を基本とする（詳細は [`overview.md`](./overview.md)）
- レース中のめくり・着順確定はルール演算（タイマーではない）

## 命名

| 対象 | 規則 | 例 |
|------|------|-----|
| 機能ID | kebab-case | `card-seed` |
| API-ID | `API-<FEATURE>-<NNN>` | `API-BETTING-001` |
| 画面ID | `SCR-phone-<NNN>` / `SCR-display-<NNN>` | `SCR-phone-001` |
| 要件ID | `REQ-<feature短縮>-<NNN>` | `REQ-lobby-001` |

機能詳細設計では、画面を Phone / Display で分けて SCR を採番する。

## ワイヤー参照

| パス | 内容 |
|------|------|
| [`../../wireframes/README.md`](../../wireframes/README.md) | 索引・二画面対応表（正規フロー順） |
| [`../../wireframes/phone/DESIGN.md`](../../wireframes/phone/DESIGN.md) | スマホ **ビジュアル基準**（design.md 形式） |
| [`../../wireframes/display/DESIGN.md`](../../wireframes/display/DESIGN.md) | ディスプレイ **ビジュアル基準**（design.md 形式） |
| [`../../wireframes/phone/screens.md`](../../wireframes/phone/screens.md) | スマホ画面レイアウト草案（SCR-phone-*） |
| [`../../wireframes/display/screens.md`](../../wireframes/display/screens.md) | ディスプレイ画面レイアウト草案（SCR-display-*） |
| [`../../wireframes/phone/`](../../wireframes/phone/) | スマホ側 HTML ラフ（旧順・旧語あり） |
| [`../../wireframes/display/`](../../wireframes/display/) | ディスプレイ側 PNG ラフ |

## 設計書の更新ルール

- 初回設計: 人間レビュー後に design PR で `develop` へマージ
- 実装中: AI は設計書を自動更新しない
- 軽微な調整: 人間依頼時のみ、同じ feat PR 内
- 大きな変更（REQ／画面フロー／ルール整合）: 別 design PR
