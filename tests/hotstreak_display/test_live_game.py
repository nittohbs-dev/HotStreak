"""実ルールのスナップショットで全会場画面を描画する。"""
import os
os.environ.setdefault('SDL_VIDEODRIVER', 'dummy')
from random import Random
import pygame
import pytest
from hotstreak_core.state import GameSession, Player
from hotstreak_sync.server import build_app
from hotstreak_display.app import make_views, japanese_font


@pytest.mark.parametrize('count', (3, 8))
def test_all_live_screens(count, tmp_path):
    pygame.init()
    try:
        views = make_views(japanese_font())
        runtime = build_app().state.runtime
        s = GameSession('render', [Player(str(i), name=f'参加者{i}') for i in range(count)], rng=Random(count))
        runtime.add_session(s)
        canvas = pygame.Surface((1280, 720))
        context = dict(firstIndex=1, connected=True, pending=False, dt=.3,
                       joinUrl='http://192.168.12.10:8000/join/render')
        def draw():
            snapshot = runtime.snapshot(s)
            views[s.phase].draw_live(canvas, snapshot, context)
            pygame.image.save(canvas, str(tmp_path / f'{count}-{s.phase}.png'))
            return snapshot
        draw()
        runtime.services['lobby'].advance(s)
        runtime.complete_transition(s, 'lobby')
        draw()
        runtime.services['setup-cards'].advance(s)
        runtime.complete_transition(s, 'setup-cards')
        draw()
        betting = runtime.services['betting']
        for pid in betting.order(s):
            ticket = next(t for t in betting.stock(s) if t['remaining'])
            betting.act(s, 'picks', dict(ticket, face='safe'), pid)
        draw()
        betting.advance(s)
        runtime.complete_transition(s, 'betting')
        draw()
        seed = runtime.services['card-seed']
        for p in s.players:
            seed.act(s, 'seed', {'handCardId': p.hand[0].instance_id}, p.player_id)
        draw()
        seed.advance(s)
        runtime.complete_transition(s, 'card-seed')
        draw()
        for _ in range(150):
            runtime.services['race'].advance(s)
            runtime.complete_transition(s, 'race')
            draw()
            if s.phase == 'payout':
                break
        assert s.phase == 'payout'
    finally:
        pygame.quit()
