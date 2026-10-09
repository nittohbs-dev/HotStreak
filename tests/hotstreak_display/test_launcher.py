"""通常起動もPR側のセッションと会場UIを使用する。"""
import json
import socket
from urllib.request import Request, urlopen

from hotstreak_display import app, live


def test_launcher_starts_matching_server_and_stops_it(monkeypatch):
    with socket.socket() as sock:
        sock.bind(('127.0.0.1', 0))
        port = sock.getsockname()[1]
    monkeypatch.setattr('sys.argv', ['hotstreak', '--windowed', '--bind-host', '127.0.0.1',
                                    '--public-host', '192.0.2.10', '--port', str(port)])
    received = []

    def display(argv):
        received.extend(argv)
        base = argv[argv.index('--server') + 1]
        with urlopen(Request(base + '/api/sessions', data=b'{}',
                             headers={'Content-Type': 'application/json'})) as response:
            session = json.load(response)
        with urlopen(base + session['joinUrl']) as response:
            assert 'connection=session' in response.url
        assert '--windowed' in argv and '--new' in argv
        assert argv[argv.index('--join-origin') + 1] == f'http://192.0.2.10:{port}'

    monkeypatch.setattr(live, 'main', display)
    app.main()
    assert received
    with socket.socket() as sock:
        assert sock.connect_ex(('127.0.0.1', port)) != 0


def test_fullscreen_uses_native_resolution_and_window_preserves_canvas(monkeypatch):
    import pygame
    from unittest.mock import Mock
    mode = Mock()
    monkeypatch.setattr(pygame.display, 'set_mode', mode)
    live.open_display()
    mode.assert_called_with((0, 0), pygame.FULLSCREEN)
    live.open_display(True)
    mode.assert_called_with((1280, 720), pygame.RESIZABLE)
    assert live.fitted_canvas_size(1920, 1080) == (1920, 1080)
    assert live.fitted_canvas_size(1920, 1200) == (1920, 1080)
    assert live.fitted_canvas_size(1024, 768) == (1024, 576)


def test_launcher_forwards_explicit_fullscreen_and_rejects_conflicting_modes(monkeypatch):
    import pytest
    received = []
    monkeypatch.setattr(live, 'main', lambda argv: received.extend(argv))
    monkeypatch.setattr('sys.argv', ['hotstreak', '--fullscreen', '--server', 'http://localhost:8011'])
    app.main()
    assert '--fullscreen' in received and '--windowed' not in received
    monkeypatch.setattr('sys.argv', ['hotstreak', '--fullscreen', '--windowed'])
    with pytest.raises(SystemExit) as error:
        app.main()
    assert error.value.code == 2
