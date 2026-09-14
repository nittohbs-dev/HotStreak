"""Issue #27: Python/PygameでDisplay責務を検証する。"""

import importlib.util
import json
import os
from pathlib import Path
import sys
import threading
import unittest
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from unittest.mock import Mock, patch

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
SOURCE = Path(__file__).resolve().parents[2] / "src/hotstreak_display/screens/setup_cards.py"
spec = importlib.util.spec_from_file_location("setup_cards", SOURCE)
module = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = module
spec.loader.exec_module(module)
pygame = module.pygame


class ScreenTests(unittest.TestCase):
    def setUp(self):
        self.advance, self.transition = Mock(), Mock()
        self.screen = module.DisplaySetupCardsScreen(self.advance, self.transition)
        self.enter = pygame.event.Event(pygame.KEYDOWN, key=pygame.K_RETURN)

    def test_all_player_counts_and_state_replacement(self):
        for players in range(3, 9):
            with self.subTest(players=players):
                payload = module.demo_state(players)
                payload["hands"] = [{"private": "never render"}]
                self.screen.handle_message("setup.state", payload)
                self.assertEqual(len(self.screen.cards), 18 - players)
                self.assertEqual(self.screen.player_count, players)
                self.assertTrue(self.screen.can_advance)
                self.assertFalse(hasattr(self.screen, "hands"))

    def test_enter_requires_dealt_and_suppresses_duplicate(self):
        self.screen.handle_event(self.enter)
        payload = module.demo_state(4)
        payload.update(dealt=False, faceUpCards=[])
        self.screen.handle_message("setup.state", payload)
        self.screen.handle_event(self.enter)
        self.advance.assert_not_called()
        self.screen.handle_message("setup.state", module.demo_state(4))
        self.screen.handle_event(self.enter)
        self.screen.handle_event(self.enter)
        self.advance.assert_called_once()
        self.transition.assert_not_called()

    def test_ack_transitions_once_and_ignores_late_state(self):
        self.screen.handle_message("setup.state", module.demo_state(4))
        self.screen.handle_message("setup.advanced", {"phase": "betting"})
        self.screen.handle_message("setup.advanced", {"phase": "betting"})
        self.screen.handle_message("setup.state", module.demo_state(3))
        self.screen.handle_event(self.enter)
        self.transition.assert_called_once_with("betting")
        self.advance.assert_not_called()
        self.assertEqual(len(self.screen.cards), 14)

    def test_disconnect_blocks_until_snapshot(self):
        self.screen.handle_message("setup.state", module.demo_state(4))
        self.screen.handle_message("disconnected", {})
        self.screen.handle_event(self.enter)
        self.advance.assert_not_called()
        self.screen.handle_message("setup.state", module.demo_state(4))
        self.screen.handle_event(self.enter)
        self.advance.assert_called_once()

    def test_http_error_allows_retry_without_transition(self):
        self.screen.handle_message("setup.state", module.demo_state(4))
        self.screen.handle_event(self.enter)
        self.screen.handle_message("error", {"message": "準備中です"})
        self.assertFalse(self.screen.pending)
        self.assertEqual(self.screen.error, "準備中です")
        self.transition.assert_not_called()

    def test_bad_state_cannot_advance(self):
        for mutate in (lambda p: p.update(playerCount=10),
                       lambda p: p.update(dealt="true"),
                       lambda p: p["faceUpCards"].pop(),
                       lambda p: p["faceUpCards"].__setitem__(1, p["faceUpCards"][0])):
            payload = module.demo_state(4)
            mutate(payload)
            self.screen.handle_message("setup.state", payload)
            self.assertFalse(self.screen.can_advance)
            self.assertTrue(self.screen.error)

    def test_draw_maximum_cards_and_long_labels(self):
        pygame.font.init()
        try:
            view = module.DisplaySetupRoot()
        except RuntimeError:
            self.skipTest("日本語フォント未配置")
        payload = module.demo_state(3)
        payload["faceUpCards"][0]["effectLabel"] = "非常に長い効果の説明" * 12
        self.screen.handle_message("setup.state", payload)
        surface = pygame.Surface((1280, 720))
        view.draw(surface, self.screen)
        self.assertNotEqual(surface.get_at((70, 210)), surface.get_at((0, 0)))
        self.assertNotEqual(surface.get_at((1005, 493)), surface.get_at((0, 0)))


class ConnectionTests(unittest.TestCase):
    def test_real_http_snapshot_and_advance(self):
        requests = []

        class Handler(BaseHTTPRequestHandler):
            def log_message(self, *args):
                pass

            def do_GET(self):
                requests.append(("GET", self.path))
                self.send_response(200)
                self.end_headers()
                self.wfile.write(json.dumps(module.demo_state(8)).encode())

            def do_POST(self):
                requests.append(("POST", self.path))
                self.send_response(200)
                self.end_headers()
                self.wfile.write(b'{"phase":"betting"}')

        server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        try:
            connection = module.SetupConnection(f"http://127.0.0.1:{server.server_port}", "session 27")
            snapshot = connection._request("GET", "setup")
            self.assertEqual(len(snapshot["faceUpCards"]), 10)
            connection._advance()
            self.assertEqual(connection.messages.get_nowait(), ("setup.advanced", {"phase": "betting"}))
            self.assertEqual(requests, [("GET", "/api/sessions/session%2027/setup"),
                                        ("POST", "/api/sessions/session%2027/advance")])
        finally:
            server.shutdown()
            server.server_close()
            thread.join()

    def test_worker_subscribes_and_delivers_updated_cards(self):
        connection = module.SetupConnection("http://localhost:8000", "s27")
        ws = Mock()
        def receive():
            connection.stop.set()
            return json.dumps({"type": "setup.state", "payload": module.demo_state(8)})
        ws.recv.side_effect = receive
        with patch.object(module.websocket, "create_connection", return_value=ws), \
                patch.object(connection, "_request", return_value=module.demo_state(3)):
            connection._run()
        screen = module.DisplaySetupCardsScreen(Mock(), Mock())
        screen.handle_message(*connection.messages.get_nowait())
        self.assertEqual(len(screen.cards), 15)
        screen.handle_message(*connection.messages.get_nowait())
        self.assertEqual(len(screen.cards), 10)
        ws.close.assert_called_once()


if __name__ == "__main__":
    unittest.main()
