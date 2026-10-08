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
