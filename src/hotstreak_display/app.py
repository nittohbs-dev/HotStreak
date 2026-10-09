"""HotStreak 会場アプリ。同期サーバと実画面をまとめて起動する。"""
import argparse
import socket
import threading
import time
from pathlib import Path
import pygame
from .screens.lobby import LobbyView


def lan_address():
    # 外へデータは送らず、OSの経路選択からLANアドレスを取得する。
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
        try:
            sock.connect(('192.0.2.1', 9))
            return sock.getsockname()[0]
        except OSError:
            return '127.0.0.1'


def japanese_font(explicit=None):
    if explicit:
        return explicit
    found = pygame.font.match_font('yugothic,meiryo,notosanscjk,ipagothic,hiraginosans')
    if found:
        return found
    for name in ('*W3.ttc', '*Unicode.ttf'):
        for directory in (Path('/System/Library/Fonts'), Path('/System/Library/Fonts/Supplemental')):
            found = list(directory.glob(name))
            if found:
                return str(found[0])
    return None


def make_views(font):
    from .screens.setup_cards import LiveView as SetupView
    from .screens.betting import LiveView as BettingView
    from .screens.card_seed import LiveView as SeedView
    from .screens.race_live import LiveView as RaceView
    from .screens.payout import LiveView as PayoutView
    return {'lobby': LobbyView(font), 'setup-cards': SetupView(font), 'betting': BettingView(font),
            'card-seed': SeedView(font), 'race': RaceView(font), 'payout': PayoutView(font)}


def main():
    parser = argparse.ArgumentParser(description='HotStreak: QR参加から3レースまで')
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument('--windowed', action='store_true', help='1280×720のウィンドウ表示')
    mode.add_argument('--fullscreen', action='store_true', help='モニター全面に表示（既定）')
    parser.add_argument('--font')
    parser.add_argument('--server', help='既に起動している会場サーバ（未指定なら同時起動）')
    parser.add_argument('--port', type=int, default=8000)
    parser.add_argument('--bind-host', default='0.0.0.0', help='会場サーバーの待受アドレス')
    parser.add_argument('--public-host', help='スマホからアクセスする会場PCのIPアドレス')
    args = parser.parse_args()
    public_base = None
    server = None
    server_thread = None
    if not args.server:
        import uvicorn
        from hotstreak_sync.app import create_app
        address = args.public_host or lan_address()
        public_base = f'http://{address}:{args.port}'
        server = uvicorn.Server(uvicorn.Config(create_app(), host=args.bind_host, port=args.port, log_level='warning'))
        server_thread = threading.Thread(target=server.run, daemon=True)
        server_thread.start()
        deadline = time.monotonic()+8
        while not server.started and server_thread.is_alive() and time.monotonic() < deadline:
            time.sleep(.05)
        if not server.started:
            raise RuntimeError('同期サーバを起動できません。ポートの使用状況を確認してください。')
        loopback = '[::1]' if ':' in args.bind_host else '127.0.0.1'
        args.server = f'http://{loopback}:{args.port}'
        print(f'参加用サーバ: {public_base}', flush=True)
    from .live import main as run_display
    options = ['--server', args.server]
    if public_base:
        options += ['--join-origin', public_base, '--new']
    elif args.public_host:
        options += ['--join-origin', f'http://{args.public_host}:{args.port}']
    if args.windowed:
        options.append('--windowed')
    elif args.fullscreen:
        options.append('--fullscreen')
    if args.font:
        options += ['--font', args.font]
    try:
        run_display(options)
    finally:
        if server:
            server.should_exit = True
            server_thread.join(timeout=5)


if __name__ == '__main__':
    main()
