import os
os.environ.setdefault('SDL_VIDEODRIVER', 'dummy')
os.environ.setdefault('SDL_AUDIODRIVER', 'dummy')
from types import SimpleNamespace
from random import Random
from unittest.mock import Mock
import pygame
import pytest
from hotstreak_display.audio import GameAudio, MixerAudio, EFFECTS, ROOT
from hotstreak_display.live import RacePresentation
from hotstreak_display.screens.race_live import LiveRaceModel
from hotstreak_core.session import GameSession


class Output:
    def __init__(self):
        self.events = []

    def bgm(self, name):
        self.events.append(('bgm', name))

    def effect(self, name):
        self.events.append(('effect', name))

    def close(self):
        self.events.append(('close', None))


def test_audio_waits_for_visual_effect_and_does_not_repeat_on_poll():
    out = Output()
    audio = GameAudio(out)
    state = dict(phase='lobby', revision=0)
    audio.update(state, None, .1)
    audio.update(state, None, .1)
    assert out.events == [('bgm', 'waiting')]
    model = SimpleNamespace(moving=False, revealing=False, visual_positions=[2.]*4,
                            facing=[1]*4, fallen=[False]*4, status=['racing']*4)
    state = dict(phase='race', revision=1, raceIndex=1, revealed=0)
    audio.update(state, model, .1, 3.4)
    for delay in [3.3, 2.4, 1.4, .4, .3, 0.]:
        audio.update(state, model, .1, delay)
    assert out.events.count(('effect', 'tick')) == 3
    assert out.events.count(('effect', 'go')) == 1
    state.update(revision=2, revealed=1)
    model.moving = model.revealing = True
    audio.update(state, model, .1, 0.)
    audio.update(state, model, .1, 0.)
    assert out.events.count(('effect', 'card')) == 1
    assert ('effect', 'reverse') not in out.events
    model.revealing = False
    model.facing[0] = -1
    model.fallen[1] = True
    model.visual_positions[0] = 1.9
    audio.update(state, model, .1, 0.)
    assert ('effect', 'reverse') in out.events
    assert ('effect', 'tumble') in out.events
    assert ('effect', 'step') in out.events
    before = list(out.events)
    audio.update(state, model, .1, 0.)
    assert out.events == before


def test_final_goal_and_payout_wait_until_last_animation_finishes():
    out = Output()
    audio = GameAudio(out)
    model = SimpleNamespace(moving=False, revealing=False, visual_positions=[12.]*4,
                            facing=[1]*4, fallen=[False]*4, status=['racing']*4)
    audio.update(dict(phase='race', revision=2, raceIndex=1, revealed=8), model, .1, 0.)
    model.moving = model.revealing = True
    state = dict(phase='payout', revision=3, raceIndex=1, revealed=9)
    audio.update(state, model, .1, 0.)
    assert ('effect', 'payout') not in out.events
    model.moving = model.revealing = False
    model.status[0] = 'goal'
    audio.update(state, model, .1, 0.)
    audio.update(state, model, .1, 0.)
    assert out.events.count(('effect', 'goal')) == 1
    assert out.events.count(('effect', 'payout')) == 1
    assert out.events[-3:] == [('bgm', 'waiting'), ('effect', 'goal'), ('effect', 'payout')]


def model_at_start():
    return SimpleNamespace(moving=False, revealing=False, visual_positions=[2.]*4,
                           facing=[1]*4, fallen=[False]*4, status=['racing']*4)


def test_initial_payout_and_mid_race_do_not_replay_past_events():
    for phase in ('payout', 'race'):
        out = Output()
        audio = GameAudio(out)
        model = model_at_start()
        model.fallen[0], model.facing[1], model.status[2] = True, -1, 'goal'
        state = dict(phase=phase, revision=25, raceIndex=2, revealed=10)
        audio.update(state, model, .1, 0.)
        audio.update(state, model, .1, 0.)
        assert out.events == [('bgm', 'race' if phase == 'race' else 'waiting')]


def test_old_notifications_and_new_session_with_same_race_number():
    out = Output()
    audio = GameAudio(out)
    state = dict(sessionId='first', phase='race', revision=10, raceIndex=1, revealed=8)
    model = model_at_start()
    audio.update(state, model, .1, 0.)
    audio.update(dict(state, phase='betting', revision=9), None, .1)
    assert out.events == [('bgm', 'race')]
    # 同じraceIndex・低いrevisionでも別セッションの初回状態として扱う。
    model.fallen[0], model.facing[1], model.status[2] = True, -1, 'goal'
    audio.update(dict(state, sessionId='second', revision=1, revealed=4), model, .1, 0.)
    assert not any(kind == 'effect' for kind, _ in out.events)
    audio.update(dict(state, sessionId='second', revision=2, revealed=5), model, .1, 0.)
    assert out.events.count(('effect', 'card')) == 1


def test_steps_are_rate_limited_and_disqualification_is_not_goal():
    out = Output()
    audio = GameAudio(out)
    model = model_at_start()
    state = dict(phase='race', revision=1, raceIndex=1, revealed=1)
    audio.update(state, model, .01, 0.)
    for _ in range(100):
        model.visual_positions[0] += .01
        audio.update(state, model, .01, 0.)
    assert 5 <= out.events.count(('effect', 'step')) <= 6
    model.status[0] = 'dq'
    audio.update(state, model, .1, 0.)
    assert ('effect', 'goal') not in out.events
    prior = list(out.events)
    for _ in range(100):
        audio.update(state, model, .1, 0.)
    assert out.events == prior  # 停止中は足音なし。


@pytest.mark.parametrize('legacy', [False, True])
def test_three_real_races_lobby_return_and_all_eight_effects(legacy):
    """両表示モデルと実ルールを使い、フェーズごとの通知重複も再現する。"""
    out = Output()
    audio = GameAudio(out)
    session = GameSession(rng=Random(37))
    player = session.join()
    model = None

    def present():
        nonlocal model
        session.revision += 1
        state = session.snapshot()
        if state['phase'] == 'race' or (not legacy and state['phase'] == 'payout'):
            if legacy:
                if model is None:
                    model = LiveRaceModel()
                model.apply(state)
            elif model is None or model.race != state['raceIndex']:
                model = RacePresentation(state)
            else:
                model.receive(state)
        else:
            model = None
        # 実描画の30fpsと同じ更新刻み。通信がなくても表示中の音は進む。
        for _ in range(150):
            if model:
                (model.tick if legacy else model.update)(1/30)
            audio.update(state, model, 1/30, None if legacy else 0.)
        return state

    present()
    session.advance()
    present()
    session.advance()
    for race in range(1, 4):
        present()
        while session.turn < len(session.order):
            key = next(k for k, used in session.stock.items() if used < 3)
            session.pick(session.order[session.turn], dict(ticketId=key,
                ticketKind='mascot' if key in ('blue', 'orange', 'yellow', 'salmon') else 'side', face='safe'))
        if race == 3:
            session.double(player.player_id, player.tickets[0]['ticketInstanceId'])
        session.advance()
        present()
        session.seed(player.player_id, player.hand[0].instance_id)
        session.advance()
        present()
        if not legacy:
            for delay in (3.5, 2.5, 1.5, .5):
                audio.update(session.snapshot(), model, .1, delay)
        before_payout = out.events.count(('effect', 'payout'))
        for _ in range(100):
            session.advance()
            present()
            if session.phase == 'payout':
                break
        assert session.phase == 'payout'
        assert out.events.count(('effect', 'payout')) == before_payout+1
        session.advance()
        present()
    assert session.phase == 'lobby'
    names = {name for kind, name in out.events if kind == 'effect'}
    assert {'confirm', 'card', 'step', 'tumble', 'reverse', 'goal', 'payout'} <= names
    assert ('countdown' if legacy else 'go') in names
    assert out.events.count(('bgm', 'race')) == 3
    audio.close()
    assert out.events[-1] == ('close', None)


@pytest.fixture
def mixer(monkeypatch):
    stub = Mock()
    stub.get_init.return_value = (44100, -16, 2)
    monkeypatch.setattr(pygame, 'mixer', stub)
    return stub


def test_mixer_volume_loop_and_no_restart_between_waiting_phases(mixer):
    output = MixerAudio()
    assert output.enabled
    assert mixer.Sound.call_count == len(EFFECTS)
    volumes = [call.args[0] for call in mixer.Sound.return_value.set_volume.call_args_list]
    assert volumes.count(.28) == 1
    assert volumes.count(.68) == len(EFFECTS)-1
    audio = GameAudio(output)
    for revision, phase in enumerate(['lobby', 'setup-cards', 'betting', 'card-seed']):
        audio.update(dict(phase=phase, revision=revision), None, .1)
    assert mixer.music.load.call_count == 1
    mixer.music.set_volume.assert_called_with(.40)
    mixer.music.play.assert_called_once_with(-1, fade_ms=350)
    output.bgm('race')
    mixer.music.set_volume.assert_called_with(.50)
    assert mixer.music.play.call_count == 2
    output.close()
    output.close()
    mixer.stop.assert_called_once()


def test_no_audio_device_is_nonfatal(mixer, caplog):
    mixer.get_init.return_value = None
    mixer.init.side_effect = pygame.error('device unavailable')
    output = MixerAudio()
    output.bgm('race')
    output.effect('card')
    output.close()
    assert not output.enabled
    assert not mixer.music.play.called
    assert len(caplog.records) == 1


def test_missing_one_effect_preserves_other_audio(mixer, caplog):
    def load(path):
        if path.endswith('se_04_tumble.wav'):
            raise FileNotFoundError(path)
        return Mock()
    mixer.Sound.side_effect = load
    output = MixerAudio()
    assert output.enabled and 'tumble' not in output.sounds
    for _ in range(3):
        output.effect('tumble')
    output.effect('card')
    output.sounds['card'].play.assert_called_once()
    output.bgm('waiting')
    mixer.music.play.assert_called_once()
    assert len(caplog.records) == 1


def test_music_load_or_play_failure_is_isolated(mixer, caplog):
    output = MixerAudio()
    mixer.music.load.side_effect = [None, OSError('race missing'), None]
    output.bgm('waiting')
    output.bgm('race')
    output.bgm('race')
    output.bgm('waiting')
    output.bgm('race')
    assert mixer.music.load.call_count == 3
    assert mixer.music.play.call_count == 2
    assert len(caplog.records) == 1
    # 他の曲や効果音は継続。失敗した曲の代わりに前の曲を流し続けない。
    assert mixer.music.stop.call_count == 4
    output.effect('card')
    output.sounds['card'].play.assert_called_once()
    mixer.music.load.side_effect = None
    mixer.music.play.side_effect = pygame.error('device lost')
    output.bgm('waiting')
    assert len(caplog.records) == 2


def test_effect_and_shutdown_device_failure_do_not_escape(mixer, caplog):
    output = MixerAudio()
    output.sounds['card'].play.side_effect = pygame.error('device lost')
    output.effect('card')
    output.effect('card')
    assert 'card' not in output.sounds
    mixer.music.stop.side_effect = pygame.error('device lost')
    output.close()
    output.close()
    assert len(caplog.records) == 2


def test_bundled_assets_really_decode_and_credit_is_visible():
    pygame.init()
    try:
        output = MixerAudio()
        assert output.enabled and set(output.sounds) == set(EFFECTS)
        for name in ('waiting', 'race'):
            output.bgm(name)
            assert pygame.mixer.music.get_busy()
        for sound in output.sounds.values():
            assert sound.get_length() > 0
        audio = GameAudio(output)
        canvas = pygame.Surface((1280, 720))
        audio.draw_credit(canvas)
        assert audio.credit.get_width() < 1256
        assert audio.credit.get_height() <= 15
        credits = (ROOT/'CREDITS.txt').read_text()
        assert 'Kevin MacLeod' in credits
        assert 'https://creativecommons.org/licenses/by/4.0/' in credits
        audio.close()
    finally:
        pygame.quit()
