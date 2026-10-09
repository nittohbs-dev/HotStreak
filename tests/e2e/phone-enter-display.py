"""Phone ENTERだけで動く実HTTP会場。E2Eでは演出時計を少し速める。"""
import os
os.environ.setdefault('SDL_VIDEODRIVER', 'dummy')
os.environ.setdefault('SDL_AUDIODRIVER', 'dummy')
import json
import sys
import time
import pygame
from hotstreak_display.live import Application, Connection

config = json.load(sys.stdin)
pygame.init()
app = Application()
connection = Connection(config['origin'], config['credentials'])
connection.thread.start()
canvas = pygame.Surface((1280, 720))
deadline = time.monotonic() + 180
completed = False
try:
    while time.monotonic() < deadline:
        while not connection.messages.empty():
            kind, payload = connection.messages.get_nowait()
            if kind in ('state', 'advanced'):
                app.receive(payload, advanced=kind == 'advanced')
            else:
                app.fail(payload)
        app.update(.1)
        connection.enter_report = app.enter_report()
        command = app.take_command()
        if command:
            connection.commands.put(command)
        if app.state:
            app.draw(canvas, config['origin']+'/join/test')
            if app.state['phase'] == 'champion':
                completed = True
            if completed and app.state['phase'] == 'lobby':
                print('PASS: Phone ENTERで3レースから総合優勝・ロビーへ', flush=True)
                break
        time.sleep(.02)
    else:
        raise AssertionError('Phone ENTER E2Eが完了しませんでした')
finally:
    connection.stop.set()
    connection.thread.join(timeout=5)
    app.audio.close()
    pygame.quit()
