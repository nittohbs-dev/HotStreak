#!/usr/bin/env python3
"""wireframes の DESIGN.md を features/*/screens.md から再生成する。"""

from __future__ import annotations

import re
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
FEATURES = REPO / "docs/design/hotstreak/features"
FEATURE_ORDER = ("lobby", "setup-cards", "betting", "card-seed", "race", "payout")

PHONE_PREFIX = "SCR-phone-"
DISPLAY_PREFIX = "SCR-display-"

PHONE_HEADER = """# 画面設計: スマホ（横断）

見た目ラフ: [hotstreak-wireframes.html](./hotstreak-wireframes.html) / [screen-01-title.html](./screen-01-title.html)  
ルール・流れ: [`../../hotstreak/00-project/overview.md`](../../hotstreak/00-project/overview.md)

## このファイルの位置づけ

| 層 | パス | 役割 |
|----|------|------|
| 正本（機能・REQ・API） | `docs/design/hotstreak/features/<機能ID>/screens.md` | spec-browser・実装 Issue が参照 |
| 横断ビュー（本ファイル） | `docs/design/wireframes/phone/DESIGN.md` | スマホ側 SCR を一覧・遷移で見る |
| 旧草案 | [screens.md](./screens.md) | **廃止**（本ファイルへ統合済み） |

**矛盾時は機能別 `screens.md` を優先する。** 本ファイルは `tools/design/build_wireframe_design_md.py` で再生成できる。

進行: **時間遷移なし**。次フェーズは **全員揃い** または **ラズパイ Enter**。

"""

DISPLAY_HEADER = """# 画面設計: ディスプレイ（横断）

見た目ラフ: [試合開始前設計.png](./試合開始前設計.png) / [ゲーム進行画面-ディスプレイ側.png](./ゲーム進行画面-ディスプレイ側.png)  
ルール・流れ: [`../../hotstreak/00-project/overview.md`](../../hotstreak/00-project/overview.md)

## このファイルの位置づけ

| 層 | パス | 役割 |
|----|------|------|
| 正本（機能・REQ・API） | `docs/design/hotstreak/features/<機能ID>/screens.md` | spec-browser・実装 Issue が参照 |
| 横断ビュー（本ファイル） | `docs/design/wireframes/display/DESIGN.md` | ディスプレイ側 SCR を一覧・遷移で見る |
| 旧草案 | [screens.md](./screens.md) | **廃止**（本ファイルへ統合済み） |

**矛盾時は機能別 `screens.md` を優先する。** 本ファイルは `tools/design/build_wireframe_design_md.py` で再生成できる。

"""

PHONE_FLOW = """
## 画面遷移（スマホ）

```mermaid
flowchart LR
  p001[SCR-phone-001] -->|全員名前_or_Enter| wait[公開カード待機]
  wait -->|setup.advanced| p002[SCR-phone-002]
  p002 -->|全員2枚_or_Enter| p003[SCR-phone-003]
  p003 -->|全員仕込み_or_Enter| p004[SCR-phone-004]
  p004 -->|race.finished| p005[SCR-phone-005]
  p004 -.->|ボタン| p004b[SCR-phone-004b]
  p005 -->|Enter レース1-2| p002
  p005 -->|Enter レース3| p001
```

## 実装ソース（Pygame / Web）

| SCR-ID | パス | 状態 |
|--------|------|------|
| SCR-phone-001 | （未配置） | 未実装 |
| （待機） | Phone シェル | setup-cards 中は専用 SCR なし |
| SCR-phone-002 | （未配置） | 未実装 |
| SCR-phone-003 | （未配置） | 未実装 |
| SCR-phone-004 / 004b | （未配置） | 未実装 |
| SCR-phone-005 | （未配置） | 未実装 |

"""

DISPLAY_FLOW = """
## 画面遷移（ディスプレイ）

```mermaid
flowchart LR
  d001[SCR-display-001] --> d002[SCR-display-002]
  d002 --> d003[SCR-display-003]
  d003 --> d004[SCR-display-004]
  d004 --> d005[SCR-display-005]
  d005 --> d006[SCR-display-006]
  d006 -->|レース1or2| d003
  d006 -->|レース3| d001
```

## 実装ソース（Pygame）

| SCR-ID | パス | 状態 |
|--------|------|------|
| SCR-display-001 | `src/hotstreak_display/screens/lobby.py`（予定） | 未実装 |
| SCR-display-002 | [`src/hotstreak_display/screens/setup_cards.py`](../../../src/hotstreak_display/screens/setup_cards.py) | 一部実装 |
| SCR-display-003 | （未配置） | 未実装 |
| SCR-display-004 | （未配置） | 未実装 |
| SCR-display-005 | （未配置） | 未実装 |
| SCR-display-006 | （未配置） | 未実装 |

"""


def parse_table(text: str, header_marker: str) -> list[dict[str, str]]:
    lines = text.splitlines()
    start = None
    for i, line in enumerate(lines):
        if header_marker in line and line.strip().startswith("|"):
            start = i
            break
    if start is None:
        return []
    headers = [c.strip() for c in lines[start].strip().strip("|").split("|")]
    rows: list[dict[str, str]] = []
    for line in lines[start + 1 :]:
        if not line.startswith("|"):
            break
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if all(set(c) <= set("-:") for c in cells):
            continue
        rows.append(dict(zip(headers, cells, strict=False)))
    return rows


def scr_sections(text: str, id_prefix: str) -> list[tuple[str, str]]:
    pattern = re.compile(rf"^## ({re.escape(id_prefix)}[^:]+):(.+)$", re.MULTILINE)
    out: list[tuple[str, str]] = []
    matches = list(pattern.finditer(text))
    for i, m in enumerate(matches):
        end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
        out.append((m.group(1).strip(), text[m.start() : end].strip()))
    return out


def sort_scr_key(scr_id: str) -> tuple:
    base = scr_id.split(":")[0].replace("## ", "").strip()
    m = re.match(r"SCR-(phone|display)-(\d+)(.*)", base)
    if not m:
        return (9, 0, base)
    suffix = m.group(3) or ""
    return (0 if m.group(1) == "phone" else 1, int(m.group(2)), suffix)


def build(side: str) -> str:
    prefix = PHONE_PREFIX if side == "phone" else DISPLAY_PREFIX
    header = PHONE_HEADER if side == "phone" else DISPLAY_HEADER
    flow = PHONE_FLOW if side == "phone" else DISPLAY_FLOW

    uc_rows: list[dict[str, str]] = []
    scr_list_rows: list[dict[str, str]] = []
    matrix_rows: list[dict[str, str]] = []
    bodies: list[tuple[str, str]] = []

    for fid in FEATURE_ORDER:
        path = FEATURES / fid / "screens.md"
        if not path.is_file():
            continue
        text = path.read_text(encoding="utf-8")
        for row in parse_table(text, "UC-ID"):
            screens = row.get("必要な画面", "")
            if side == "phone":
                if "SCR-phone" in screens or "Phone" in screens:
                    uc_rows.append(row)
            elif "SCR-display" in screens:
                uc_rows.append(row)
        for row in parse_table(text, "主な操作"):
            if row.get("SCR-ID", "").startswith(prefix):
                scr_list_rows.append(row)
        for row in parse_table(text, "主コンポーネント"):
            if row.get("SCR-ID", "").startswith(prefix):
                matrix_rows.append(row)
        for scr_id, body in scr_sections(text, prefix):
            bodies.append((scr_id, body))

    bodies.sort(key=lambda x: sort_scr_key(x[0]))

    parts = [header]

    parts.append("## ユースケースと画面の対応\n\n")
    parts.append("| UC-ID | 必要な画面 |\n|-------|------------|\n")
    seen_uc: set[str] = set()
    for row in uc_rows:
        uc = row.get("UC-ID", "")
        if uc in seen_uc:
            continue
        seen_uc.add(uc)
        parts.append(f"| {uc} | {row.get('必要な画面', '')} |\n")
    parts.append("\n")

    parts.append("## 画面一覧\n\n")
    parts.append("| SCR-ID | 名前 | ルート | 主な操作 | 呼ぶAPI |\n")
    parts.append("|--------|------|--------|----------|---------|\n")
    for row in scr_list_rows:
        parts.append(
            f"| {row['SCR-ID']} | {row['名前']} | {row['ルート']} | {row['主な操作']} | {row['呼ぶAPI']} |\n"
        )
    parts.append("\n")

    parts.append(flow)

    parts.append("## 対応マトリクス\n\n")
    parts.append("| SCR-ID | 画面 | 関連REQ | 呼ぶAPI | 主コンポーネント | 遷移先 |\n")
    parts.append("|--------|------|---------|---------|------------------|--------|\n")
    for row in matrix_rows:
        parts.append(
            f"| {row['SCR-ID']} | {row['画面']} | {row['関連REQ']} | {row['呼ぶAPI']} | "
            f"{row['主コンポーネント']} | {row['遷移先']} |\n"
        )
    parts.append("\n---\n\n")

    for _, body in bodies:
        parts.append(body + "\n\n---\n\n")

    return "".join(parts).rstrip() + "\n"


def main() -> None:
    phone_out = REPO / "docs/design/wireframes/phone/DESIGN.md"
    display_out = REPO / "docs/design/wireframes/display/DESIGN.md"
    phone_out.write_text(build("phone"), encoding="utf-8")
    display_out.write_text(build("display"), encoding="utf-8")
    print(f"wrote {phone_out.relative_to(REPO)}")
    print(f"wrote {display_out.relative_to(REPO)}")


if __name__ == "__main__":
    main()
