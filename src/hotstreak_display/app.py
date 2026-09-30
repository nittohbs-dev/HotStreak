"""HotStreak 会場アプリ。同期サーバと実画面をまとめて起動する。"""
import argparse
import socket
import threading
import time
from pathlib import Path
from queue import Empty
import pygame
from .connection import DisplayConnection
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
    return {'lobby': LobbyView(font), 'setup-cards': SetupView(font), 'betting': BettingView(font),
            'card-seed': SeedView(font), 'race': RaceView(font)}


def main():
    parser = argparse.ArgumentParser(description='HotStreak: QR参加から3レースまで')
    parser.add_argument('--windowed', action='store_true')
    parser.add_argument('--font')
    parser.add_argument('--server', help='既に起動している会場サーバ（未指定なら同時起動）')
    parser.add_argument('--port', type=int, default=8000)
    parser.add_argument('--public-host', help='スマホからアクセスする会場PCのIPアドレス')
    args = parser.parse_args()
    server = None
    server_thread = None
    if not args.server:
        import uvicorn
        from hotstreak_sync.server import build_app
        address = args.public_host or lan_address()
        public_base = f'http://{address}:{args.port}'
        server = uvicorn.Server(uvicorn.Config(build_app(public_base), host='0.0.0.0', port=args.port, log_level='warning'))
        server_thread = threading.Thread(target=server.run, daemon=True)
        server_thread.start()
        deadline = time.monotonic()+8
        while not server.started and server_thread.is_alive() and time.monotonic() < deadline:
            time.sleep(.05)
        if not server.started:
            raise RuntimeError('同期サーバを起動できません。ポートの使用状況を確認してください。')
        args.server = f'http://127.0.0.1:{args.port}'
        print(f'参加用サーバ: {public_base}', flush=True)
    connection = DisplayConnection(args.server)
    pygame.init()
    try:
        views = make_views(japanese_font(args.font))
        display = pygame.display.set_mode((1280, 720), pygame.RESIZABLE if args.windowed else pygame.FULLSCREEN)
        pygame.display.set_caption('ホットストリーク — 会場')
        canvas = pygame.Surface((1280, 720))
        clock = pygame.time.Clock()
        state = {'phase': 'lobby', 'revision': -1, 'players': []}
        context = {'joinUrl': '', 'firstIndex': 0}
        connected, pending, error = False, False, ''
        connection.thread.start()
        running = True
        while running:
            dt = clock.tick(30)/1000
            while True:
                try:
                    kind, payload = connection.messages.get_nowait()
                except Empty:
                    break
                if kind == 'session':
                    context.update(payload)
                    print('参加URL: '+payload['joinUrl'], flush=True)
                elif kind == 'state' and payload.get('revision', -1) >= state['revision']:
                    state = payload
                elif kind == 'connected':
                    connected, pending, error = True, False, ''
                elif kind == 'ack':
                    pending, error = False, ''
                elif kind in ('error', 'disconnected'):
                    pending, error = False, payload.get('message', '')
                    if kind == 'disconnected':
                        connected = False
            for event in pygame.event.get():
                if event.type == pygame.QUIT or (event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE):
                    running = False
                elif event.type == pygame.KEYDOWN and not getattr(event, 'repeat', False):
                    if event.key in (pygame.K_LEFT, pygame.K_RIGHT) and state['phase'] == 'setup-cards':
                        context['firstIndex'] = (context['firstIndex'] + (1 if event.key == pygame.K_RIGHT else -1)) % max(1, len(state['players']))
                    elif event.key in (pygame.K_RETURN, pygame.K_KP_ENTER) and connected and not pending:
                        first = state['players'][context['firstIndex'] % len(state['players'])]['playerId'] if state['players'] else None
                        connection.advance(state, first)
                        pending = True
            context.update(connected=connected, pending=pending, dt=dt)
            view = views.get(state['phase'])
            if view:
                view.draw_live(canvas, state, context)
            else:
                canvas.fill((12, 15, 20))
                views['lobby'].text(canvas, '次の画面を準備しています', (300, 300), 32)
            if error or not connected or pending:
                pygame.draw.rect(canvas, (15, 17, 22), (0, 650, 1280, 70))
                message = error or ('進行を確認しています…' if pending else '接続しています…')
                views['lobby'].text(canvas, message, (30, 674), 20, (244, 151, 128), 1220)
            width, height = display.get_size()
            scale = min(width/1280, height/720)
            size = max(1, int(1280*scale)), max(1, int(720*scale))
            display.fill((0, 0, 0))
            display.blit(pygame.transform.scale(canvas, size), ((width-size[0])//2, (height-size[1])//2))
            pygame.display.flip()
    finally:
        if connection.thread.is_alive():
            connection.close()
        pygame.quit()
        if server:
            server.should_exit = True
            server_thread.join(timeout=5)


if __name__ == '__main__':
    main()
