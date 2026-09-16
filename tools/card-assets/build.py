"""実物カード一覧の表示素材を生成する。ゲームの効果処理は含めない。"""
import json
import os
from pathlib import Path

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
import pygame

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "assets/images/cards"
DATA = ROOT / "data/cards"
W, H = 240, 336
COLORS = {"blue": ((29, 57, 128), (219, 235, 166)),
          "orange": ((241, 124, 40), (83, 30, 103)),
          "salmon": ((241, 191, 132), (161, 44, 48)),
          "yellow": ((244, 206, 46), (86, 36, 40)),
          "green": ((44, 104, 65), (220, 238, 191))}
LABELS = {"blue": "青", "orange": "オレンジ", "salmon": "サーモン", "yellow": "黄", "green": "緑"}
EFFECTS = [("swerve_1", "1", "移動後に{dir}へ"), ("swerve_2", "2", "移動後に{dir}へ"),
           ("swerve_3", "3", "移動後に{dir}へ"), ("move_2", "2", "移動"),
           ("move_minus_2", "−2", "移動"), ("move_3", "3", "移動"),
           ("recover_1", "1", "復帰して移動"), ("recover_2", "2", "復帰して移動"),
           ("turn", "↶", "方向転換"), ("fall", "↓", "転倒"), ("star", "★", "スター")]
EVENTS = [
    ("knockout", "マスコットはノックアウトされる？", "転倒中に再び転倒して失格"),
    ("out_of_bounds", "マスコットはコース外に出る？", "後方・側面・短縮部分を含む"),
    ("disqualified", "1体以上が失格する？", ""),
    ("same_space", "2体が同時に同じマスに止まる？", "その瞬間の失格は含めない"),
    ("fallen_two", "2体以上が同時に転倒する？", ""),
    ("crawl_final", "最終区間でマスコットが這う？", "最後の実線からゴールまで・出入りを含む"),
    ("finish_two", "2体以上が同時にゴール直前に並ぶ？", "ゴール直前のマス"),
    ("empty_final", "1位が決まる時、最終区間は空？", "最後の実線からゴールまで"),
    ("gobbler_bottom", "GOBBLERは下位2位に入る？", "最下位または下から2番目"),
    ("hurley_bottom", "HURLEYは下位2位に入る？", "最下位または下から2番目"),
    ("mum_bottom", "MUMは下位2位に入る？", "最下位または下から2番目"),
    ("dangle_bottom", "DANGLEは下位2位に入る？", "最下位または下から2番目"),
]


def build():
    pygame.font.init()
    font_path = pygame.font.match_font("yugothic,meiryo,notosanscjk,ipagothic")
    if not font_path:
        raise RuntimeError("日本語フォントが必要です")
    fonts = {size: pygame.font.Font(font_path, size) for size in (16, 20, 24, 32, 52)}
    for font in fonts.values():
        font.set_bold(True)
    def text(surf, words, y, size, color, width=208):
        lines, line = [], ""
        for char in words:
            if fonts[size].size(line + char)[0] > width:
                lines.append(line)
                line = char
            else:
                line += char
        lines.append(line)
        for line in lines:
            img = fonts[size].render(line, False, color)
            surf.blit(img, ((W - img.get_width()) // 2, y))
            y += size + 6
        return y
    source = pygame.image.load(str(ROOT / "assets/images/characters/card_mascots_source.png"))
    icons = pygame.Surface((512, 128))
    icons.fill((13, 20, 28))
    rects = {}
    for index, color in enumerate(("blue", "orange", "salmon", "yellow")):
        sx, sy = source.get_width() // 2, source.get_height() // 2
        crop = source.subsurface((index % 2 * sx, index // 2 * sy, sx, sy))
        # 64pxに落としてから整数倍拡大し、ドットの粒を統一。
        icon = pygame.transform.scale(pygame.transform.scale(crop, (64, 64)), (128, 128))
        icons.blit(icon, (index * 128, 0))
        rects[color] = [index * 128, 0, 128, 128]
    pygame.image.save(icons, ROOT / "assets/images/characters/card_mascots.png")
    entries, images = [], []
    def add(card_id, kind, color, effect, number, label, quantity=1, note=""):
        surf = pygame.Surface((W, H))
        base, ink = COLORS.get(color, ((16, 20, 26), (231, 226, 211)))
        border = ink if effect == "recover_2" and color != "green" else (183, 165, 131)
        surf.fill(border)
        pygame.draw.rect(surf, base, (5, 5, W-10, H-10))
        pygame.draw.rect(surf, ink, (11, 11, W-22, H-22), 2)
        for x in range(19, W-19, 12):
            pygame.draw.rect(surf, ink, (x, 16, 4, 3))
            pygame.draw.rect(surf, ink, (x, H-19, 4, 3))
        if kind == "race":
            text(surf, number, 25, 52, ink)
            text(surf, label, 88, 20, ink)
            pygame.draw.rect(surf, (13, 20, 28), (18, 128, 204, 133))
            if color == "green":
                for i in range(4):
                    sprite = pygame.transform.scale(icons.subsurface((i*128, 0, 128, 128)), (64, 64))
                    surf.blit(sprite, (56 + i%2*64, 130+i//2*64))
                text(surf, "衝突なし・ゴール不可", 280, 16, ink)
            else:
                surf.blit(icons.subsurface(rects[color]), (56, 130))
                text(surf, LABELS[color], 280, 24, ink)
        elif kind == "event":
            text(surf, "SIDE BET", 30, 20, (223, 191, 134))
            pygame.draw.line(surf, (223, 191, 134), (32, 70), (208, 70), 2)
            end = text(surf, label, 102, 24, ink)
            if note:
                text(surf, note, max(234, end + 16), 16, (189, 192, 193))
        else:
            for y in range(32, H-28, 10):
                for x in range(26, W-24, 10):
                    pygame.draw.rect(surf, (45, 49, 55), (x, y, 2, 2))
            pygame.draw.polygon(surf, (223, 191, 134), ((120, 62), (197, 167), (120, 272), (43, 167)), 3)
            text(surf, "?", 133, 52, (223, 191, 134))
        index = len(entries)
        entries.append(dict(id=card_id, kind=kind, color=color, effect=effect, label=label, quantity=quantity,
                            note=note, rect=[index%8*W, index//8*H, W, H]))
        images.append(surf)
    for color in ("blue", "orange", "salmon", "yellow"):
        direction = "左" if color in ("blue", "yellow") else "右"
        for effect, number, label in EFFECTS:
            add(f"{color}_{effect}", "race", color, effect, number, label.format(dir=direction))
    for effect, number, label, quantity in (("move_1", "1", "全員移動", 2), ("move_2", "2", "全員移動", 2),
            ("move_3", "3", "全員移動", 2), ("move_minus_2", "−2", "全員移動", 1),
            ("recover_2", "2", "全員復帰して移動", 1), ("recover_3", "3", "全員復帰して移動", 1)):
        add(f"green_{effect}", "race", "green", effect, number, label, quantity, "衝突なし・ゴール不可")
    for key, label, note in EVENTS:
        add(f"event_{key}", "event", "black", key, "", label, note=note)
    add("card_back", "back", "black", "back", "", "共通裏面（モック用オリジナル）", 0)
    sheet = pygame.Surface((W*8, H*8))
    sheet.fill((9, 12, 17))
    for image, entry in zip(images, entries):
        sheet.blit(image, entry["rect"][:2])
    OUT.mkdir(parents=True, exist_ok=True)
    DATA.mkdir(parents=True, exist_ok=True)
    pygame.image.save(sheet, OUT / "cards_atlas.png")
    catalog = dict(image="assets/images/cards/cards_atlas.png", icons_image="assets/images/characters/card_mascots.png",
                   cell_size=[W,H], icons=rects, cards=entries, mascot_name_mapping=None)
    (DATA / "catalog.json").write_text(json.dumps(catalog, ensure_ascii=False, indent=2)+"\n", encoding="utf-8")
    print(f"Generated {len(entries)} images / {sum(e['quantity'] for e in entries)} physical cards")


if __name__ == "__main__":
    build()
