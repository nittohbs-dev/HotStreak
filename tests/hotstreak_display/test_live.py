import os
os.environ.setdefault('SDL_VIDEODRIVER', 'dummy')
os.environ.setdefault('SDL_AUDIODRIVER', 'dummy')
from random import Random
from pathlib import Path
import pygame
from hotstreak_core.session import GameSession
from hotstreak_display.live import Application, RacePresentation


def test_race_history_only_contains_current_deck_cycle():
    presentation = object.__new__(RacePresentation)
    cards = [dict(cardId=f'card-{index}') for index in range(17)]
    presentation.set_card(dict(currentCard=None, remaining=13, revealed=17, revealedCards=cards))
    assert presentation.card_history == ['card-15', 'card-16']

    presentation.set_card(dict(currentCard=None, remaining=15, revealed=15, revealedCards=cards[:15]))
    assert presentation.card_history == []


def test_server_snapshots_render_existing_screens_and_animation(tmp_path):
    pygame.init()
    try:
        app = Application()
        canvas = pygame.Surface((1280, 720))
        s = GameSession(rng=Random(3))
        def draw():
            s.revision += 1
            app.receive(s.snapshot())
            for _ in range(40):
                app.update(.1)
                app.draw(canvas, 'http://localhost:8000/join/test')
            assert not app.error
        for _ in range(8):
            s.join()
        draw()
        s.advance()
        draw()
        s.advance()
        draw()
        while s.turn < len(s.order):
            key = next(k for k, count in s.stock.items() if count < 3)
            s.pick(s.order[s.turn], dict(ticketId=key, ticketKind='mascot' if key in ('blue','orange','yellow','salmon') else 'side', face='safe'))
        s.advance()
        draw()
        for p in s.players:
            s.seed(p.player_id, p.hand[0].instance_id)
        s.advance()
        draw()
        while s.phase == 'race':
            s.advance()
            draw()
        assert s.phase == 'payout'
        pygame.image.save(canvas, tmp_path/'payout-live.png')
        s.advance()
        draw()
    finally:
        pygame.quit()
