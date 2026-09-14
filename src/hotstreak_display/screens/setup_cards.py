"""SCR-display-002: 公開カードの表示とEnter連携（Issue #27）。"""

from __future__ import annotations

import argparse
from dataclasses import dataclass
import json
from pathlib import Path
from queue import Empty, Queue
import threading
from urllib.error import HTTPError, URLError
from urllib.parse import quote, urlsplit, urlunsplit
from urllib.request import Request, urlopen

import pygame
import websocket


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

    def text(self, surface, value, pos, size=20, color=(235, 233, 224), max_width=None):
        value = str(value)
        font = self.fonts[size]
        if max_width:
            while value and font.size(value)[0] > max_width:
                value = value[:-2] + "…" if len(value) > 1 else ""
        surface.blit(font.render(value, True, color), pos)

    def draw(self, surface, state):
        surface.fill((18, 24, 30))
        # 素材なしでも読める描画。背景はラフの暗い部屋を意識した色調。
        for y in range(0, 720, 48):
            pygame.draw.line(surface, (24, 31, 37), (0, y), (1280, y))
        pygame.draw.rect(surface, (213, 170, 94), (40, 34, 5, 91))
        self.text(surface, "HOT STREAK  /  SETUP", (64, 30), 16, (213, 170, 94))
        self.text(surface, "場のカード（公開）", (60, 53), 44)
        count = f"参加者 {state.player_count} 人  /  公開 {len(state.cards)} 枚" if state.player_count else "公開カードを取得しています"
        self.text(surface, count, (64, 111), 20, (170, 180, 188))
        self.text(surface, "マスコットと効果を確認して、マ券選びの参考にしてください。", (64, 147), 20)
        self.renderFaceUpGrid(surface, state.cards)
        pygame.draw.line(surface, (66, 73, 78), (48, 637), (1232, 637))
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
        self.text(surface, footer, (64, 660), 24,
                  (244, 151, 128) if state.error else (235, 214, 169), 1152)

    def renderFaceUpGrid(self, surface, cards):
        for index, card in enumerate(cards):
            x, y = 64 + index % 5 * 234, 201 + index // 5 * 141
            rect = pygame.Rect(x, y, 216, 125)
            pygame.draw.rect(surface, (34, 42, 49), rect, border_radius=8)
            pygame.draw.rect(surface, (83, 89, 93), rect, width=1, border_radius=8)
            # 色は装飾。マスコット名とlaneも表示して色だけに依存しない。
            mascot_colors = dict(zip(("Gobbler", "Hurley", "Dangle", "Mum"), self.COLORS))
            color = mascot_colors.get(card.mascot, (185, 190, 199))
            pygame.draw.rect(surface, color, (x, y + 10, 4, 104))
            self.text(surface, card.mascot, (x + 15, y + 12), 24, color, 184)
            self.text(surface, card.effect, (x + 15, y + 49), 20, max_width=184)
            self.text(surface, f"LANE {card.lane}", (x + 15, y + 94), 16, (158, 169, 180), 184)


def demo_state(players):
    """画面確認用の架空データ。抽選・配布ルールの実装ではない。"""
    names = ("Gobbler", "Hurley", "Dangle", "Mum")
    effects = ("前へ 2マス", "方向転換", "前へ 1マス", "転倒")
    return {"phase": "setup-cards", "playerCount": players, "dealt": True,
            "faceUpCards": [{"cardId": f"demo-{i}", "mascot": names[i % 4],
                             "effectLabel": effects[i % 4], "lane": i % 4 + 1}
                            for i in range(18 - players)]}


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
