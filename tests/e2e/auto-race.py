"""実HTTP接続の会場アプリをEnterイベントで操作するE2E補助。"""
import os
os.environ.setdefault('SDL_VIDEODRIVER', 'dummy')
os.environ.setdefault('SDL_AUDIODRIVER', 'dummy')
os.environ['PYGAME_HIDE_SUPPORT_PROMPT'] = '1'
import json
import sys
import time
import pygame
from hotstreak_display.live import Application, Connection


def press(app):
    was_running = app.auto_running
    for kind in (pygame.KEYUP, pygame.KEYDOWN):
        app.handle_event(pygame.event.Event(kind, key=pygame.K_RETURN, repeat=False))
    if not was_running:
        app.update(1.)


def main():
    config = json.load(sys.stdin)
    pygame.init()
    app = Application()
    connection = Connection(config['origin'], config['credentials'])
    canvas = pygame.Surface((1280, 720))
    connection.thread.start()
    manual_started = started = paused = resumed = False
    pause_frames = sent = 0
    deadline = time.monotonic() + 90
    try:
        while time.monotonic() < deadline:
            while not connection.messages.empty():
                kind, data = connection.messages.get_nowait()
                if kind in ('state', 'advanced'):
                    app.receive(data, advanced=kind == 'advanced')
                else:
                    raise AssertionError(data)
            if app.state and not manual_started and app.start_delay <= 0:
                assert not app.auto_running
                app.handle_event(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_RETURN))
                app.update(.2)
                app.handle_event(pygame.event.Event(pygame.KEYUP, key=pygame.K_RETURN))
                manual_started = True
            elif (manual_started and not started and app.state['revealed'] == 1
                  and not app.pending and not app.moving):
                assert not app.auto_running
                press(app)
                started = True
            if started and not paused and app.race and app.race.revealing:
                press(app)
                assert not app.auto_running
                paused = True
            app.update(.1)  # 演出時計のみ高速化。HTTPとPhoneは実接続。
            if paused and not resumed and not app.moving and not app.pending:
                pause_frames += 1
                assert app.take_command() is None
                if pause_frames >= 15:
                    press(app)
                    resumed = True
            command = app.take_command()
            if command:
                assert command['phase'] == 'race', '配当を自動で進めない'
                sent += 1
                connection.commands.put(command)
            if app.state:
                app.draw(canvas, 'http://localhost/join/test')
            if app.state and app.state['phase'] == 'payout' and not app.moving:
                assert paused and resumed and not app.auto_running
                assert app.take_command() is None
                print(json.dumps(dict(race=app.state['raceIndex'], requests=sent, manual=True, paused=True, resumed=True)))
                return
            time.sleep(.005)
        raise AssertionError('自動進行が90秒以内に完了しない')
    finally:
        connection.stop.set()
        connection.thread.join(timeout=5)
        pygame.quit()


if __name__ == '__main__':
    main()
