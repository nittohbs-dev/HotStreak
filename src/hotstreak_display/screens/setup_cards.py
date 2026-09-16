"""SCR-display-002: 公開カードの表示とEnter連携（Issue #27）。"""

from __future__ import annotations

import argparse
from dataclasses import dataclass
import json
from pathlib import Path
from queue import Empty, Queue
import threading
import sys
from urllib.error import HTTPError, URLError
from urllib.parse import quote, urlsplit, urlunsplit
from urllib.request import Request, urlopen

import pygame
import websocket

if __package__:
    from ..card_assets import CardAssets, COLOR_LABELS
else:
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
    from card_assets import CardAssets, COLOR_LABELS


@dataclass(frozen=True)
class FaceUpCard:
    card_id: str
    mascot: str
    effect: str
    lane: str


class DisplaySetupCardsScreen:
    """CLS-setup-010。同期層や次画面の実装を持たない。"""

    def __init__(self, advance, on_advanced):
        self.advance = advance
        self.on_advanced = on_advanced
        self.cards: tuple[FaceUpCard, ...] = ()
        self.player_count = 0
        self.dealt = False
        self.connected = False
        self.pending = False
        self.advanced = False
        self.error = ""

    @property
    def can_advance(self):
        return self.connected and self.dealt and not self.pending and not self.advanced

    def handle_message(self, kind, payload):
        if self.advanced:
            return
        if kind == "setup.state":
            # 非公開手札は取り込まない。入力検証後にまとめて反映する。
            try:
                count = payload["playerCount"]
                dealt = payload["dealt"]
                raw_cards = payload["faceUpCards"]
                if payload.get("phase", "setup-cards") != "setup-cards":
                    raise ValueError("phase")
                if type(count) is not int or not 3 <= count <= 8:
                    raise ValueError("playerCount")
                if type(dealt) is not bool or not isinstance(raw_cards, list):
                    raise ValueError("state")
                cards = tuple(FaceUpCard(
                    str(c["cardId"]), str(c["mascot"]),
                    str(c["effectLabel"]), str(c["lane"]),
                ) for c in raw_cards)
                if len(cards) > 15 or (dealt and len(cards) != 18 - count):
                    raise ValueError("card count")
                if len({c.card_id for c in cards}) != len(cards):
                    raise ValueError("duplicate card")
            except (KeyError, TypeError, ValueError):
                self.dealt = False
                self.error = "公開カードの情報を確認できません。再接続してください。"
                return
            self.cards, self.player_count, self.dealt = cards, count, dealt
            self.connected = True
            self.error = ""
        elif kind == "setup.advanced":
            if payload.get("phase") == "betting":
                self.advanced = True
                self.pending = False
                self.on_advanced("betting")
        elif kind == "disconnected":
            self.connected = False
            self.pending = False
            self.error = "接続が切れました。再接続しています…"
        elif kind == "error":
            self.pending = False
            self.error = payload["message"]

    def handle_event(self, event):
        if event.type == pygame.KEYDOWN and event.key in (pygame.K_RETURN, pygame.K_KP_ENTER):
            if self.can_advance:
                self.pending = True
                self.error = ""
                self.advance()


class SetupConnection:
    """API-SETUP-001/002とWSをUIスレッドの外で処理する。"""

    def __init__(self, server, session_id):
        parts = urlsplit(server)
        if parts.scheme not in ("http", "https") or not parts.netloc or parts.query or parts.fragment:
            raise ValueError("server は http(s)://host[:port] 形式で指定してください")
        self.base = server.rstrip("/")
        self.session = quote(session_id, safe="")
        self.ws_url = urlunsplit(("wss" if parts.scheme == "https" else "ws",
                                 parts.netloc, parts.path.rstrip("/") +
                                 f"/ws/sessions/{self.session}", "", ""))
        self.messages = Queue()
        self.commands = Queue()
        self.stop = threading.Event()
        self.thread = threading.Thread(target=self._run, daemon=True)

    def start(self):
        self.thread.start()

    def advance(self):
        self.commands.put("advance")

    def close(self):
        self.stop.set()
        self.thread.join(timeout=6)

    def _request(self, method, suffix):
        request = Request(f"{self.base}/api/sessions/{self.session}/{suffix}",
                          data=b"{}" if method == "POST" else None,
                          headers={"Content-Type": "application/json"}, method=method)
        with urlopen(request, timeout=4) as response:
            return json.load(response)

    def _advance(self):
        try:
            result = self._request("POST", "advance")
            # HTTP成功もサーバの確定結果。WSの重複通知は画面側で無視する。
            if result.get("phase") == "betting":
                self.messages.put(("setup.advanced", result))
            else:
                self.messages.put(("error", {"message": "進行結果を確認できません。再接続してください。"}))
        except HTTPError as error:
            message = {404: "セッションが見つかりません",
                       409: "準備中、またはこの操作はできません",
                       500: "カードの準備に失敗しました。セッションを再作成してください。"}
            self.messages.put(("error", {"message": message.get(error.code, "進行に失敗しました。もう一度Enterを押してください。")}))

    def _run(self):
        while not self.stop.is_set():
            ws = None
            try:
                # 購読を先に確立し、GETとの間に発生したイベントも取りこぼさない。
                ws = websocket.create_connection(self.ws_url, timeout=4)
                snapshot = self._request("GET", "setup")
                self.messages.put(("setup.state", snapshot))
                ws.settimeout(0.2)
                while not self.stop.is_set():
                    try:
                        self.commands.get_nowait()
                    except Empty:
                        pass
                    else:
                        self._advance()
                    try:
                        raw = ws.recv()
                        if not raw:
                            raise ConnectionError("closed")
                        event = json.loads(raw)
                        # WS封筒は同期側未実装のためREADMEに接続契約を明記。
                        kind = event["type"]
                        payload = event["payload"]
                        if kind in ("setup.state", "setup.advanced") and isinstance(payload, dict):
                            self.messages.put((kind, payload))
                    except websocket.WebSocketTimeoutException:
                        continue
            except HTTPError as error:
                self.messages.put(("disconnected", {}))
                message = {404: "セッションが見つかりません",
                           409: "公開カードのフェーズではありません",
                           500: "カードの準備に失敗しました。セッションを再作成してください。"}
                self.messages.put(("error", {"message": message.get(error.code, "サーバへの接続に失敗しました")}))
            except (OSError, URLError, ValueError, KeyError, TypeError, websocket.WebSocketException):
                self.messages.put(("disconnected", {}))
            finally:
                if ws:
                    ws.close()
                # 切断前のEnterを、再接続後に遅れて実行しない。
                while not self.commands.empty():
                    try:
                        self.commands.get_nowait()
                    except Empty:
                        break
            self.stop.wait(1)


class DisplaySetupRoot:
    """CMP-setup-001〜003: 画面・案内・公開カードグリッド。"""

    WIDTH, HEIGHT = 1280, 720
    COLORS = ((231, 125, 77), (94, 178, 225), (226, 189, 85), (165, 185, 117))

    def __init__(self, font_path=None):
        path = font_path or pygame.font.match_font("yugothic,meiryo,notosanscjk,ipagothic")
        if not path:
            raise RuntimeError("日本語フォントが必要です。--font にTTF/OTFファイルを指定してください。")
        self.fonts = {size: pygame.font.Font(path, size) for size in (16, 20, 24, 32, 44)}
        for font in self.fonts.values():
            font.set_bold(True)
        self.background = self.make_room()
        self.card_assets = CardAssets()

    @staticmethod
    def make_room():
        """低解像度で描いた部屋を整数倍拡大し、ラフのドット感に寄せる。"""
        room = pygame.Surface((320, 180))
        room.fill((17, 18, 23))
        for row in range(18):
            y = 20 + row * 7
            for col in range(17):
                x = col * 21 - (10 if row % 2 else 0)
                shade = (row * 11 + col * 7) % 12
                pygame.draw.rect(room, (29 + shade, 24 + shade // 2, 27 + shade // 3), (x, y, 20, 6))
                pygame.draw.line(room, (49, 34, 32), (x + 1, y), (x + 18, y))
        # 奥の壁・柱・配管。
        for x in (17, 294):
            pygame.draw.rect(room, (13, 15, 20), (x, 20, 9, 139))
            pygame.draw.rect(room, (76, 43, 35), (x + 2, 20, 2, 137))
            for y in (30, 76, 126):
                pygame.draw.rect(room, (109, 67, 43), (x, y, 8, 2))
        for x in (4, 310):
            pygame.draw.rect(room, (15, 29, 38), (x, 55, 6, 82))
            pygame.draw.line(room, (59, 69, 67), (x, 55), (x, 137))
        # 左右の壁に古い額と椅子。
        for x in (28, 274):
            pygame.draw.rect(room, (83, 53, 38), (x, 48, 16, 29))
            pygame.draw.rect(room, (149, 113, 67), (x + 1, 49, 14, 27), 1)
            pygame.draw.rect(room, (43, 35, 30), (x + 3, 51, 10, 23))
            for y in (54, 60, 66):
                pygame.draw.rect(room, (103, 75, 44), (x + 5, y, 6, 2))
            pygame.draw.rect(room, (10, 16, 23), (x, 117, 15, 20))
            pygame.draw.rect(room, (39, 46, 52), (x + 1, 117, 12, 2))
            pygame.draw.rect(room, (51, 36, 31), (x - 1, 136, 19, 3))
            for dx in (0, 13):
                pygame.draw.rect(room, (12, 13, 16), (x + dx, 139, 2, 9))
        # 奥行きのある床。
        pygame.draw.polygon(room, (46, 31, 29), ((0, 149), (320, 149), (320, 180), (0, 180)))
        for x in range(-180, 501, 37):
            pygame.draw.line(room, (17, 20, 24), (160 + (x - 160) // 3, 149), (x, 180), 1)
        for y in (151, 156, 164, 176):
            pygame.draw.line(room, (87, 51, 36), (0, y), (320, y))
            pygame.draw.line(room, (20, 21, 25), (0, y + 1), (320, y + 1))
        # ランプの光は背景のみ。カードの文字コントラストは一定にする。
        glow = pygame.Surface((320, 180), pygame.SRCALPHA)
        for radius in range(36, 3, -3):
            pygame.draw.circle(glow, (243, 147, 54, 2 + (36 - radius) // 3), (160, 28), radius)
        room.blit(glow, (0, 0))
        pygame.draw.line(room, (11, 13, 17), (160, 17), (160, 24), 2)
        pygame.draw.polygon(room, (108, 66, 36), ((151, 28), (156, 24), (164, 24), (169, 28)))
        pygame.draw.rect(room, (255, 210, 119), (152, 29, 16, 2))
        pygame.draw.rect(room, (255, 239, 174), (156, 29, 8, 2))
        return pygame.transform.scale(room, (1280, 720))

    def mascot_icon(self, surface, name, center, scale):
        sprite = self.card_assets.icon(name, (scale * 16, scale * 16))
        if sprite is not None:
            surface.blit(sprite, sprite.get_rect(center=center))
            return
        patterns = {
            "Gobbler": (".##.....##.", "####...####", ".#########.", "..#######..", "..#.#.#.#..", "..#######..", "...##.##...", "..#######..", ".#########.", "..#######..", "..##...##.."),
            "Hurley": (".....##....", "...######..", "..########.", "###.#.####.", ".##########", "..########.", "...######..", "....####...", "...##..##..", "..##....##.", "..........."),
            "Dangle": (".....##....", "....####...", "..########.", "..#.#.####.", "..#########", "...######..", ".#########.", "..#######..", "...#####...", "...##.##...", "..###.###.."),
            "Mum": ("..##...##..", "..##...##..", "..##...##..", "..#######..", "..#.#.#.#..", "..#######..", "...#####...", "..#######..", ".#########.", "..#######..", "..##...##.."),
        }
        colors = dict(zip(patterns, self.COLORS))
        pattern = patterns.get(name, ("....###....", "...#####...", "..#######..", ".#########.", "..#######..", "...#####...", "....###...."))
        color = colors.get(name, (190, 182, 164))
        ox, oy = center[0] - 11 * scale // 2, center[1] - len(pattern) * scale // 2
        for row, line in enumerate(pattern):
            for col, pixel in enumerate(line):
                if pixel == "#":
                    pygame.draw.rect(surface, (7, 11, 17), (ox + col * scale + 3, oy + row * scale + 4, scale, scale))
        for row, line in enumerate(pattern):
            for col, pixel in enumerate(line):
                if pixel == "#":
                    tint = tuple(min(255, c + 24) for c in color) if col < 4 else color
                    pygame.draw.rect(surface, tint, (ox + col * scale, oy + row * scale, scale, scale))

    def text(self, surface, value, pos, size=20, color=(235, 233, 224), max_width=None):
        value = str(value)
        font = self.fonts[size]
        if max_width:
            while value and font.size(value)[0] > max_width:
                value = value[:-2] + "…" if len(value) > 1 else ""
        surface.blit(font.render(value, True, color), pos)

    def draw(self, surface, state):
        surface.blit(self.background, (0, 0))
        pygame.draw.rect(surface, (9, 12, 17), (20, 16, 1240, 65))
        pygame.draw.rect(surface, (202, 190, 161), (20, 16, 1240, 65), 2)
        self.text(surface, "場のカード（公開）", (43, 25), 32)
        self.text(surface, "HOT STREAK", (1020, 39), 16, (200, 165, 108))
        pygame.draw.rect(surface, (12, 15, 20), (160, 125, 960, 64))
        self.text(surface, "参加人数に応じて、場に出るカードの枚数が変わります。", (203, 130), 24)
        count = f"参加者 {state.player_count} 人  ／  公開カード {len(state.cards)} 枚" if state.player_count else "公開カードを取得しています"
        self.text(surface, count, (453, 162), 20, (223, 191, 134))
        self.renderFaceUpGrid(surface, state.cards)
        pygame.draw.rect(surface, (10, 13, 19), (160, 650, 960, 51))
        pygame.draw.rect(surface, (124, 99, 67), (160, 650, 960, 51), 2)
        if state.error:
            footer = state.error
        elif state.advanced:
            footer = "マ券ドラフトへ進みます"
        elif state.pending:
            footer = "進行を確認しています…"
        elif state.can_advance:
            footer = "ENTER  →  マ券ドラフトへ"
        else:
            footer = "カードを準備しています…"
        self.text(surface, footer, (184, 661), 24,
                  (244, 151, 128) if state.error else (235, 214, 169), 910)

    def renderFaceUpGrid(self, surface, cards):
        columns = 8 if len(cards) > 10 else 5
        width = 132 if columns == 8 else 150
        height = round(width * 336 / 240)
        step = 145 if columns == 8 else 192
        start = (1280 - (columns - 1) * step - width) // 2
        for index, card in enumerate(cards):
            x, y = start + index % columns * step, 207 + index // columns * (height + 12)
            asset_id = card.card_id if card.card_id in self.card_assets.cards else "card_back"
            surface.blit(self.card_assets.card(asset_id, (width, height)), (x, y))
            if asset_id == "card_back":
                self.text(surface, card.effect, (x + 8, y + height // 2), 16, max_width=width - 16)


def demo_state(players):
    """画面確認用の架空データ。抽選・配布ルールの実装ではない。"""
    colors = ("blue", "orange", "salmon", "yellow", "green")
    assets = CardAssets()
    choices = [f"{color}_{effect}" for effect in ("move_2", "move_3", "recover_2") for color in colors]
    return {"phase": "setup-cards", "playerCount": players, "dealt": True,
            "faceUpCards": [{"cardId": key, "mascot": COLOR_LABELS[assets.cards[key]["color"]],
                             "effectLabel": assets.cards[key]["label"], "lane": i % 4 + 1}
                            for i, key in enumerate(choices[:18 - players])]}


def main():
    parser = argparse.ArgumentParser(description="Issue #27 公開カード画面")
    parser.add_argument("--server", default="http://127.0.0.1:8000")
    parser.add_argument("--session")
    parser.add_argument("--demo", action="store_true")
    parser.add_argument("--players", type=int, choices=range(3, 9), default=4)
    parser.add_argument("--font", help="日本語TTF/OTFのパス")
    parser.add_argument("--windowed", action="store_true")
    parser.add_argument("--screenshot", type=Path, help="デモ画面をPNG保存して終了")
    args = parser.parse_args()
    if not args.demo and not args.session:
        parser.error("--session または --demo が必要です")
    if args.screenshot and not args.demo:
        parser.error("--screenshot は --demo と併用してください")
    pygame.init()
    connection = None
    try:
        canvas = pygame.Surface((1280, 720))
        view = DisplaySetupRoot(args.font)
        transitioned = []
        connection = None if args.demo else SetupConnection(args.server, args.session)
        state = DisplaySetupCardsScreen(
            connection.advance if connection else lambda: state.handle_message("setup.advanced", {"phase": "betting"}),
            transitioned.append,
        )
        if args.demo:
            state.handle_message("setup.state", demo_state(args.players))
        if args.screenshot:
            view.draw(canvas, state)
            pygame.image.save(canvas, args.screenshot)
            return
        display = pygame.display.set_mode((1280, 720), pygame.RESIZABLE if args.windowed else pygame.FULLSCREEN)
        pygame.display.set_caption("ホットストリーク — 公開カード" + (" [DEMO]" if args.demo else ""))
        if connection:
            connection.start()
        clock = pygame.time.Clock()
        running = True
        while running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT or (event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE):
                    running = False
                else:
                    state.handle_event(event)
            if connection:
                while True:
                    try:
                        state.handle_message(*connection.messages.get_nowait())
                    except Empty:
                        break
            view.draw(canvas, state)
            width, height = display.get_size()
            scale = min(width / 1280, height / 720)
            size = (max(1, int(1280 * scale)), max(1, int(720 * scale)))
            display.fill((12, 16, 20))
            display.blit(pygame.transform.smoothscale(canvas, size), ((width - size[0]) // 2, (height - size[1]) // 2))
            pygame.display.flip()
            if transitioned:
                print("setup.advanced: betting（次画面は別Issue）")
                running = False
            clock.tick(30)
    finally:
        if connection and connection.thread.is_alive():
            connection.close()
        pygame.quit()


if __name__ == "__main__":
    main()
