"""既存の会場画面にサーバ確定状態を表示する実行入口。"""
import argparse
import json
from math import ceil
from pathlib import Path
from queue import Queue, Empty
from threading import Thread, Event
from types import SimpleNamespace
from urllib.request import Request, urlopen
from urllib.error import HTTPError
from uuid import uuid4
import pygame
from .screens.setup_cards import DisplaySetupRoot, DisplaySetupCardsScreen
from .screens.betting import DisplayBettingRoot, BettingPreview, PlayerPreview, MASCOTS
from .screens.card_seed import DisplaySeedRoot, SeedPreview
from .screens.race import View as RaceView, Model as RaceModel, COLORS
from .screens.payout import View as PayoutView


class Connection:
    def __init__(self, server, credentials):
        self.base = server.rstrip('/') + '/api/sessions/' + credentials['sessionId']
        self.token = credentials['displayToken']
        self.messages, self.commands = Queue(), Queue()
        self.stop = Event()
        self.thread = Thread(target=self.run, daemon=True)

    def request(self, body=None):
        headers = {'Content-Type': 'application/json', 'X-Display-Token': self.token}
        if body is not None:
            headers['Idempotency-Key'] = str(uuid4())
        request = Request(self.base + ('/advance' if body is not None else ''),
                          data=json.dumps(body).encode() if body is not None else None, headers=headers)
        with urlopen(request, timeout=4) as response:
            return json.load(response)

    def run(self):
        while not self.stop.is_set():
            try:
                try:
                    body = self.commands.get_nowait()
                except Empty:
                    body = None
                self.messages.put(('advanced' if body is not None else 'state', self.request(body)))
            except HTTPError as exc:
                try:
                    message = json.load(exc).get('message', '操作できません')
                except (ValueError, OSError):
                    message = 'サーバから状態を取得できません'
                self.messages.put(('offline' if exc.code >= 500 else 'error', message))
            except (OSError, ValueError):
                self.messages.put(('offline', '接続が切れました。再接続しています…'))
            self.stop.wait(.2)


class RacePresentation(RaceModel):
    """効果判定を持たず、サーバから届いた前後の座標間だけを補間する。"""
    def __init__(self, snapshot):
        super().__init__(SimpleNamespace(state='start'))
        self.snapshot = snapshot
        self.race = snapshot['raceIndex']
        self.reveal_elapsed = 1.60
        self.reveal_snapshot = None
        self.pending_collapse = None
        self.apply(snapshot['mascots'])
        self.removed = snapshot['course']['removed']
        self.visual_positions = list(self.positions)
        self.visual_lanes = list(self.lanes)
        self.last_revealed = snapshot['revealed']
        self.set_card(snapshot)
        self.state = 'start' if snapshot['revealed'] == 0 else 'running'

    def apply(self, mascots):
        rows = {m['color']: m for m in mascots}
        self.positions = tuple(rows[c]['position'] for c in COLORS)
        self.lanes = [rows[c]['lane'] for c in COLORS]
        self.facing = [rows[c]['facing'] for c in COLORS]
        self.fallen = [rows[c]['fallen'] for c in COLORS]
        self.status = [rows[c]['status'] for c in COLORS]
        self.standings = [None]*4
        self.tie_ranks = {}
        occupied = sorted(((m['rank'], i) for i, c in enumerate(COLORS)
                           if (m := rows[c])['finished']), key=lambda item: item[0])
        for slot, (rank, i) in enumerate(occupied):
            self.standings[slot] = i
            self.tie_ranks[i] = rank

    def set_card(self, snapshot):
        card = snapshot['currentCard']
        revealed_cards = snapshot.get('revealedCards', [])
        cycle_used = 15 - snapshot['remaining']
        cycle_start = max(0, snapshot['revealed'] - cycle_used)
        self.card_history = [c['cardId'] for c in revealed_cards[cycle_start:]]
        self.card_id = card['cardId'] if card else 'card_back'
        self.effect = card['effectLabel'] if card else '3枚バーン済み'
        self.remaining = snapshot['remaining']
        self.action = card['effectKind'] if card else 'idle'
        if self.action.startswith('recover'):
            self.action = 'recover'
        color = card['color'] if card else None
        self.targets = list(range(4)) if color == 'green' else [COLORS.index(color)] if color in COLORS else []
        self.active = self.targets[0] if self.targets else 0

    def receive(self, snapshot):
        if snapshot['revealed'] == self.last_revealed:
            return
        self.last_revealed = snapshot['revealed']
        self.reveal_snapshot = snapshot
        self.reveal_elapsed = 0.
        self.moving = True
        self.state = 'running'

    @property
    def revealing(self):
        return self.reveal_snapshot is not None

    def begin_effect(self, snapshot):
        self.snapshot = snapshot
        self.previous, self.previous_lanes = self.positions, self.lanes[:]
        self.old_fallen = self.fallen[:]
        if self.card_history:
            self.history_flight = (self.card_history[-1], self.elapsed)
        self.set_card(snapshot)
        self.target_rows = snapshot.get('beforeShortening') or snapshot['mascots']
        rows = {m['color']: m for m in self.target_rows}
        self.positions = tuple(rows[c]['position'] for c in COLORS)
        self.lanes = [rows[c]['lane'] for c in COLORS]
        self.facing = [rows[c]['facing'] for c in COLORS]
        self.pending_collapse = snapshot['course']['removed'] > self.removed
        self.progress, self.moving, self.state = 0., True, 'running'

    def update(self, dt):
        self.elapsed += dt
        if self.revealing:
            self.reveal_elapsed += dt
            if self.reveal_elapsed < 1.60:
                return
            dt = self.reveal_elapsed - 1.60
            snapshot, self.reveal_snapshot = self.reveal_snapshot, None
            self.begin_effect(snapshot)
        if not self.moving:
            return
        self.progress = min(1., self.progress + dt/(1.8 if self.action == 'shorten' else 1.15))
        t = self.progress*self.progress*(3-2*self.progress)
        if self.action == 'recover':
            t = max(0, (self.progress-.45)/.55)
        lateral = self.action.startswith('swerve')
        forward = min(1, t/.7) if lateral else t
        sideways = max(0, (t-.7)/.3) if lateral else t
        self.visual_positions = [a+(b-a)*forward for a, b in zip(self.previous, self.positions)]
        self.visual_lanes = [a+(b-a)*sideways for a, b in zip(self.previous_lanes, self.lanes)]
        if self.progress < 1:
            return
        if self.pending_collapse:
            self.apply(self.target_rows)
            self.pending_collapse = False
            self.action, self.progress = 'shorten', 0.
            self.previous, self.previous_lanes = self.positions, self.lanes[:]
            self.targets = []
        else:
            self.apply(self.snapshot['mascots'])
            self.removed = self.snapshot['course']['removed']
            self.moving = False
            if self.action == 'shorten':
                self.card_history = []
                self.history_flight = None
                self.card_id = 'card_back'
                self.effect = '3枚バーン済み'
                self.action = 'idle'
                self.state = 'start'


class Application:
    def __init__(self, font=None):
        from .app import japanese_font
        font = japanese_font(font)
        self.views = {'lobby': DisplaySetupRoot(font), 'setup-cards': DisplaySetupRoot(font),
                      'betting': DisplayBettingRoot(font), 'card-seed': DisplaySeedRoot(font),
                      'race': RaceView(font), 'payout': PayoutView(font)}
        self.state = None
        self.race = None
        self.error = ''
        self.pending = False
        self.connected = False
        self.auto_running = False
        self.enter_held = False
        self.hold_elapsed = None
        self.focused = True
        self.manual_requested = False
        self.next_delay = 0.
        self.start_delay = 0.

    def receive(self, state, *, advanced=False):
        if self.state and state['revision'] < self.state['revision']:
            return
        if not self.connected:
            self.error = ''
        # 定期GETが先に届いても、送信中のPOSTを完了扱いにしない。
        if advanced:
            self.pending = False
        self.connected = True
        if self.state and state['revision'] == self.state['revision']:
            return
        self.error = ''
        new_race = state['phase'] == 'race' and (
            not self.state or self.state['phase'] != 'race'
            or self.state['raceIndex'] != state['raceIndex'])
        if new_race or state['phase'] != 'race':
            self.hold_elapsed = None
            self.auto_running = False
            self.next_delay = 0.
            self.manual_requested = False
        if new_race:
            self.start_delay = 3.5 if state['revealed'] == 0 else 0.
        if state['phase'] in ('race', 'payout') and state.get('course'):
            if self.race is None or self.race.race != state['raceIndex']:
                self.race = RacePresentation(state)
            else:
                self.race.receive(state)
        elif state['phase'] != 'payout':
            self.race = None
        self.state = state

    @property
    def moving(self):
        return bool(self.race and self.race.moving)

    def fail(self, message):
        self.error = message
        self.hold_elapsed = None
        self.pending = self.connected = self.auto_running = False
        self.manual_requested = False

    def handle_event(self, event):
        if event.type == pygame.WINDOWFOCUSLOST:
            self.focused = False
            self.hold_elapsed = None
            self.auto_running = False
            self.manual_requested = False
            # 押下状態を維持し、復帰時の押しっぱなしを新しい押下にしない。
        elif event.type == pygame.WINDOWFOCUSGAINED:
            self.focused = True
        elif event.type == pygame.KEYUP and event.key in (pygame.K_RETURN, pygame.K_KP_ENTER):
            if (self.hold_elapsed is not None and self.focused and self.connected
                    and self.state and self.state['phase'] == 'race'
                    and not self.pending and not self.moving):
                self.manual_requested = True
            self.hold_elapsed = None
            self.enter_held = False
        elif event.type == pygame.KEYDOWN and event.key in (pygame.K_RETURN, pygame.K_KP_ENTER):
            fresh = not self.enter_held and not getattr(event, 'repeat', False)
            self.enter_held = True
            if not fresh or not self.focused or not self.connected or not self.state:
                return
            if self.state['phase'] == 'race':
                if self.start_delay <= 0:
                    if self.auto_running:
                        self.auto_running = False
                        self.hold_elapsed = None
                    else:
                        self.hold_elapsed = 0.
            elif not self.pending and not self.moving:
                self.manual_requested = True

    def take_command(self):
        if not self.state or not self.connected or not self.focused or self.pending or self.moving:
            return None
        if self.state['phase'] == 'race':
            if self.start_delay > 0:
                return None
            if not self.manual_requested and (not self.auto_running or self.next_delay > 0):
                return None
        elif not self.manual_requested:
            return None
        self.manual_requested = False
        self.pending = True
        return dict(revision=self.state['revision'], phase=self.state['phase'])

    @property
    def race_notice(self):
        if not self.connected:
            return '通信確認中 / 自動進行を停止しました'
        if self.state['phase'] != 'race':
            return 'レース終了 / 最後のカードを表示しています'
        if self.start_delay > 0:
            return '開始準備中 / Enter操作はGOのあと'
        if self.auto_running:
            return '自動進行中 / Enterで一時停止'
        if self.pending or self.moving:
            return 'このカードの演出後に停止 / 1秒長押しで自動再開'
        if self.state['revealed'] == 0:
            return 'Enterで1枚 / 1秒長押しで自動開始'
        return '一時停止中 / Enterで1枚・1秒長押しで自動再開'

    def update(self, dt):
        if self.hold_elapsed is not None:
            self.hold_elapsed += dt
            if self.hold_elapsed >= 1.:
                self.hold_elapsed = None
                self.auto_running = True
                if not self.pending and not self.moving:
                    self.next_delay = 0.
        self.start_delay = max(0., self.start_delay - dt)
        was_moving = self.moving
        if self.race:
            self.race.update(dt)
        if was_moving and not self.moving:
            self.next_delay = .5
        elif not self.moving and not self.pending:
            self.next_delay = max(0., self.next_delay - dt)

    def draw(self, canvas, join_url):
        if not self.state:
            canvas.fill((10, 20, 30))
            return
        s = self.state
        phase = 'race' if self.moving else s['phase']
        view = self.views[phase]
        if phase == 'race':
            self.race.live = True
            self.race.start_label = (str(ceil(self.start_delay - .5))
                                     if self.start_delay > .5 else 'GO!') if self.start_delay > 0 else 'READY'
            view.draw(canvas, self.race)
            pygame.draw.rect(canvas, (3, 32, 60), (256, 22, 590, 42), border_radius=6)
            view.text(canvas, self.race_notice, (272, 32), 20, (244, 252, 255), max_width=558)
        elif phase == 'setup-cards':
            screen = DisplaySetupCardsScreen(lambda: None, lambda _: None)
            screen.handle_message('setup.state', s)
            view.draw(canvas, screen)
        elif phase == 'betting':
            players = tuple(PlayerPreview(p['displayName'], MASCOTS[i % 4], len(s['picksByPlayer'][p['playerId']]))
                            for i, p in enumerate(s['players']))
            current = next((i for i, p in enumerate(s['players']) if p['playerId'] == s['currentPlayerId']), None)
            double_wait = s['raceIndex'] == 3 and any(not v for v in s['doubleByPlayer'].values())
            stock = {t['ticketId']: t['remaining'] for t in s['stock']}
            model = SimpleNamespace(live=True, notice='', prompt_card=s['prompt']['cardId'], state=BettingPreview(
                '', s['raceIndex'], f"{s['round']}周目", s['prompt']['text'], players, current,
                tuple(stock[k] for k in (*MASCOTS, 'yes', 'no')), current is None and not double_wait, double_wait))
            view.draw(canvas, model)
        elif phase == 'card-seed':
            completed = sum(p['seeded'] for p in s['progress'])
            view.draw(canvas, SimpleNamespace(confirmed=False, state=SeedPreview('', completed,
                len(s['progress']), 18, completed == len(s['progress']),
                tuple(card['cardId'] for card in s['faceUpCards']))))
        elif phase == 'payout':
            winners = [p['displayName'] for p in s['balances'] if p['playerId'] in s['winners']]
            view.draw(canvas, SimpleNamespace(race=s['raceIndex'], confirmed=False, state='normal',
                                               standings=s['standings'], winners=winners))
        else:
            canvas.blit(view.background, (0, 0))
            view.text(canvas, 'HOT STREAK', (70, 40), 44)
            view.text(canvas, 'スマホで参加してください', (70, 120), 32)
            view.text(canvas, join_url, (70, 175), 20)
            import qrcode
            if getattr(self, 'qr_url', None) != join_url:
                qr = qrcode.make(join_url).convert('RGB')
                self.qr = pygame.image.fromstring(qr.tobytes(), qr.size, 'RGB')
                self.qr = pygame.transform.scale(self.qr, (300, 300))
                self.qr_url = join_url
            canvas.blit(self.qr, (800, 220))
            for i, p in enumerate(s['players']):
                view.text(canvas, p['displayName'] or '名前入力中…', (90, 235+i*43), 24)
            view.text(canvas, f"参加 {s['playerCount']} / 8人  ・  1人からEnter（不足分はCPU）", (70, 650), 24)
        if self.error and phase != 'race':
            pygame.draw.rect(canvas, (45, 15, 20), (20, 670, 1240, 40))
            view.text(canvas, self.error, (32, 680), 20)


def main():
    parser = argparse.ArgumentParser(description='HotStreak 会場Display（実セッション）')
    parser.add_argument('--server', default='http://127.0.0.1:8000')
    parser.add_argument('--join-origin', help='スマホから到達できる会場PCのURL')
    parser.add_argument('--session-file', type=Path, default=Path('.hotstreak-session.json'))
    parser.add_argument('--new', action='store_true')
    parser.add_argument('--windowed', action='store_true')
    parser.add_argument('--font')
    args = parser.parse_args()
    credentials = None
    if args.session_file.exists() and not args.new:
        credentials = json.loads(args.session_file.read_text(encoding='utf-8'))
        try:
            with urlopen(args.server.rstrip('/')+'/api/sessions/'+credentials['sessionId'], timeout=4):
                pass
        except HTTPError as error:
            if error.code != 404:
                raise
            credentials = None
    if credentials is None:
        with urlopen(Request(args.server.rstrip('/')+'/api/sessions', data=b'{}',
                             headers={'Content-Type': 'application/json'}), timeout=4) as response:
            credentials = json.load(response)
        args.session_file.write_text(json.dumps({k: credentials[k] for k in ('sessionId', 'displayToken')}), encoding='utf-8')
    join_url = (args.join_origin or args.server).rstrip('/')+'/join/'+credentials['sessionId']
    pygame.init()
    connection = Connection(args.server, credentials)
    connection.thread.start()
    try:
        app = Application(args.font)
        screen = pygame.display.set_mode((1280, 720), pygame.RESIZABLE if args.windowed else pygame.FULLSCREEN)
        pygame.display.set_caption('HotStreak — 会場Display')
        canvas = pygame.Surface((1280, 720))
        clock, running = pygame.time.Clock(), True
        while running:
            dt = clock.tick(60)/1000
            while not connection.messages.empty():
                kind, payload = connection.messages.get_nowait()
                if kind in ('state', 'advanced'):
                    app.receive(payload, advanced=kind == 'advanced')
                else:
                    app.fail(payload)
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                app.handle_event(event)
            app.update(dt)
            command = app.take_command()
            if command is not None:
                connection.commands.put(command)
            app.draw(canvas, join_url)
            w, h = screen.get_size()
            ratio = min(w/1280, h/720)
            size = (max(1, int(1280*ratio)), max(1, int(720*ratio)))
            screen.fill((0, 0, 0))
            screen.blit(pygame.transform.scale(canvas, size), ((w-size[0])//2, (h-size[1])//2))
            pygame.display.flip()
    finally:
        connection.stop.set()
        connection.thread.join(timeout=5)
        pygame.quit()


if __name__ == '__main__':
    main()
