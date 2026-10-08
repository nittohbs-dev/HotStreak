"""REQ-race-008: 入力から要求までの停止境界を検証する。"""
import os
os.environ.setdefault('SDL_VIDEODRIVER', 'dummy')
os.environ.setdefault('SDL_AUDIODRIVER', 'dummy')
from random import Random
import pygame
import pytest
from hotstreak_core.session import GameSession
from hotstreak_display.live import Application


def race_session():
    s = GameSession(rng=Random(3))
    s.join()
    s.advance()
    s.advance()
    while s.turn < len(s.order):
        key = next(k for k, count in s.stock.items() if count < 3)
        s.pick(s.order[s.turn], dict(ticketId=key, ticketKind='mascot' if key in ('blue', 'orange', 'yellow', 'salmon') else 'side', face='safe'))
    s.advance()
    for p in s.players:
        if p.seed is None:
            s.seed(p.player_id, p.hand[0].instance_id)
    s.advance()
    return s


def key(app, kind=pygame.KEYDOWN, repeat=False):
    app.handle_event(pygame.event.Event(kind, key=pygame.K_RETURN, repeat=repeat))


def press(app):
    was_running = app.auto_running
    key(app, pygame.KEYUP)
    key(app)
    if not was_running:
        app.update(1.)


def response(app, s):
    s.advance()
    s.revision += 1
    app.receive(s.snapshot(), advanced=True)


def finish_animation(app):
    for _ in range(100):
        if not app.moving:
            return
        app.update(.1)
    raise AssertionError('演出が完了しない')


@pytest.fixture
def live():
    pygame.init()
    s = race_session()
    app = Application()
    app.receive(s.snapshot())
    app.update(3.5)
    yield app, s
    pygame.quit()


def test_start_waits_for_go_and_new_keypress(live):
    app, s = live
    app.start_delay = 3.5
    key(app)
    app.update(3.5)
    key(app, repeat=True)
    assert not app.auto_running and app.take_command() is None
    press(app)
    assert app.auto_running
    assert app.take_command()['phase'] == 'race'
    assert app.take_command() is None
    # キーリピートおよびKEYUPなしの追加KEYDOWNは切替しない。
    key(app, repeat=True)
    key(app)
    assert app.auto_running
    # POST前のGETが届いても次の要求を出さない。
    app.receive(s.snapshot())
    assert app.pending and app.take_command() is None


@pytest.mark.parametrize('stage', ['request', 'reveal', 'effect', 'interval'])
def test_stop_does_not_send_next_card_and_resume_works(live, stage):
    app, s = live
    press(app)
    assert app.take_command()
    if stage != 'request':
        response(app, s)
    if stage == 'effect':
        app.update(1.61)
    if stage == 'interval':
        finish_animation(app)
    press(app)
    assert not app.auto_running
    if stage == 'request':
        response(app, s)
    finish_animation(app)
    app.update(1.)
    assert app.take_command() is None
    assert app.race_notice == '一時停止中 / Enterで1枚・1秒長押しで自動再開'
    press(app)
    assert app.take_command()


def test_running_waits_for_full_animation_and_half_second(live):
    app, s = live
    press(app)
    app.take_command()
    response(app, s)
    app.update(1.59)
    assert app.race.revealing and app.take_command() is None
    finish_animation(app)
    assert app.take_command() is None
    app.update(.49)
    assert app.take_command() is None
    app.update(.011)
    assert app.take_command()


def test_stop_and_resume_during_request_does_not_duplicate(live):
    app, s = live
    press(app)
    app.take_command()
    press(app)
    press(app)
    assert app.auto_running and app.take_command() is None
    response(app, s)
    assert app.take_command() is None
    finish_animation(app)
    app.update(.5)
    assert app.take_command()


@pytest.mark.parametrize('message', ['接続が切れました', '409: revision不一致'])
def test_failure_requires_fresh_state_and_explicit_restart(live, message):
    app, s = live
    press(app)
    app.take_command()
    app.fail(message)
    assert not app.auto_running and not app.connected
    press(app)
    assert app.take_command() is None
    assert '通信確認中' in app.race_notice
    # サーバでは処理成功したが応答が届かなかったケース。
    s.advance()
    s.revision += 1
    app.receive(s.snapshot())
    finish_animation(app)
    app.update(1.)
    assert not app.auto_running and app.take_command() is None
    press(app)
    assert app.take_command()['revision'] == s.revision


def test_focus_loss_and_key_repeat_cannot_restart(live):
    app, s = live
    press(app)
    app.handle_event(pygame.event.Event(pygame.WINDOWFOCUSLOST))
    assert not app.auto_running and app.take_command() is None
    app.handle_event(pygame.event.Event(pygame.WINDOWFOCUSGAINED))
    key(app, repeat=True)
    key(app)
    assert not app.auto_running
    press(app)
    assert app.take_command()


def test_final_card_key_does_not_advance_payout_and_new_race_is_off(live):
    app, s = live
    press(app)
    for _ in range(100):
        assert app.take_command()
        response(app, s)
        if s.phase == 'payout':
            break
        finish_animation(app)
        app.update(.5)
    assert s.phase == 'payout' and not app.auto_running
    press(app)  # 最終カード演出中
    finish_animation(app)
    key(app, repeat=True)
    app.update(1.)
    assert app.take_command() is None
    press(app)
    assert app.take_command()['phase'] == 'payout'
    # 新しいレースを受信した場合もOFF。
    s = race_session()
    s.race_index = 2
    snapshot = s.snapshot()
    snapshot['raceIndex'] = 2
    snapshot['revision'] = app.state['revision'] + 1
    app.receive(snapshot, advanced=True)
    app.update(4.)
    assert not app.auto_running and app.take_command() is None


def test_stop_during_shortening_waits_for_collapse(live):
    app, s = live
    press(app)
    for _ in range(60):
        assert app.take_command()
        response(app, s)
        for _ in range(100):
            if app.race.action == 'shorten' and app.moving and not app.race.revealing:
                press(app)
                assert not app.auto_running
                finish_animation(app)
                app.update(1.)
                assert app.race.removed == s.snapshot()['course']['removed']
                assert app.take_command() is None
                return
            if not app.moving:
                break
            app.update(.1)
        app.update(.5)
    raise AssertionError('短縮を経由していない')


def test_stop_on_due_frame_wins_over_next_request(live):
    app, s = live
    press(app)
    app.take_command()
    response(app, s)
    finish_animation(app)
    app.update(.49)
    press(app)  # mainと同様、入力 → 時計更新 → 要求生成の順。
    app.update(.02)
    assert app.take_command() is None


def test_focus_return_without_held_key_accepts_first_press(live):
    app, s = live
    press(app)
    key(app, pygame.KEYUP)
    app.handle_event(pygame.event.Event(pygame.WINDOWFOCUSLOST))
    app.handle_event(pygame.event.Event(pygame.WINDOWFOCUSGAINED))
    key(app)
    app.update(1.)
    assert app.auto_running and app.take_command()


def test_restart_in_middle_of_race_stays_paused(live):
    app, s = live
    s.advance()
    restarted = Application()
    restarted.receive(s.snapshot())
    restarted.update(10.)
    assert not restarted.auto_running and restarted.take_command() is None
    assert restarted.race_notice == '一時停止中 / Enterで1枚・1秒長押しで自動再開'


def test_short_press_draws_exactly_one_card_on_release(live):
    app, s = live
    key(app)
    app.update(.2)
    assert not app.auto_running and app.take_command() is None
    key(app, pygame.KEYUP)
    assert app.take_command()
    response(app, s)
    finish_animation(app)
    app.update(2.)
    assert not app.auto_running and app.take_command() is None


def test_long_press_threshold_and_release_do_not_add_manual_draw(live):
    app, s = live
    key(app)
    app.update(.99)
    assert app.take_command() is None
    app.update(.011)
    assert app.auto_running and app.take_command()
    key(app, pygame.KEYUP)
    assert not app.manual_requested and app.take_command() is None
    response(app, s)
    finish_animation(app)
    assert app.take_command() is None


def test_stop_key_held_long_does_not_restart(live):
    app, s = live
    press(app)
    press(app)
    app.update(5.)
    key(app, repeat=True)
    key(app, pygame.KEYUP)
    assert not app.auto_running and app.take_command() is None
