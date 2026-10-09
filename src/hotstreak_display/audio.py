"""REQ-audio-001 / CLS-audio-001, CLS-audio-002: 会場表示に同期する音声。"""
import logging
from math import ceil
from pathlib import Path
import pygame

ROOT = Path(__file__).resolve().parents[2] / 'assets' / 'audio'
LOGGER = logging.getLogger(__name__)
EFFECTS = {
    'confirm': 'se_01_confirm.wav', 'card': 'se_02_card_reveal.wav',
    'step': 'se_03_step.wav', 'tumble': 'se_04_tumble.wav',
    'reverse': 'se_05_reverse.wav', 'countdown': 'se_06_countdown_go.wav',
    'goal': 'se_07_goal.wav', 'payout': 'se_08_payout.wav',
    'tick': 'countdown_tick.wav', 'go': 'countdown_go.wav',
}


class MixerAudio:
    def __init__(self):
        self.enabled = False
        self.music = None
        self.failed_tracks = set()
        self.sounds = {}
        self.status = ''
        self.closed = False
        self.device_failed = False
        self._initialize()

    def _initialize(self):
        self.enabled = False
        self.music = None
        self.sounds = {}
        try:
            if not pygame.mixer.get_init():
                pygame.mixer.init(44100, -16, 2, 512)
            pygame.mixer.set_num_channels(16)
        except (pygame.error, OSError) as error:
            self.status = '音声を再接続中…'
            LOGGER.warning('音声を使用できません: %s', error)
            return
        self.enabled = True
        self.status = ''
        self.device_failed = False
        for key, name in EFFECTS.items():
            try:
                sound = pygame.mixer.Sound(str(ROOT / 'sfx' / name))
                sound.set_volume(.28 if key == 'step' else .68)
                self.sounds[key] = sound
            except (pygame.error, OSError) as error:
                LOGGER.warning('効果音 %s を読み込めません: %s', key, error)

    def bgm(self, name):
        if self.closed or name == self.music or not self.enabled:
            return
        # 失敗した曲は再試行を連発せず、別の曲・効果音は引き続き利用する。
        self.music = name
        try:
            pygame.mixer.music.stop()
            if name in self.failed_tracks:
                self.status = 'BGMを再接続中…'
                return
            pygame.mixer.music.load(str(ROOT / 'music' / ('race.mp3' if name == 'race' else 'waiting.wav')))
            pygame.mixer.music.set_volume(.50 if name == 'race' else .40)
            pygame.mixer.music.play(-1, fade_ms=350)
            self.status = ''
        except (pygame.error, OSError) as error:
            self.status = 'BGMを再接続中…'
            self.device_failed = isinstance(error, pygame.error)
            self.failed_tracks.add(name)
            LOGGER.warning('BGM %s を再生できません: %s', name, error)

    def recover(self, name):
        """REQ-play-003: 呼出側が5秒間隔を保証。正常な曲は再開しない。"""
        if self.closed:
            return
        if self.device_failed:
            pygame.mixer.quit()
        if self.device_failed or not self.enabled or not pygame.mixer.get_init():
            self._initialize()
        if not self.enabled:
            return
        try:
            if name == self.music and pygame.mixer.music.get_busy():
                return
        except pygame.error:
            self.status = '音声を再接続中…'
            self.device_failed = True
            self.enabled = False
            return
        self.music = None
        self.failed_tracks.discard(name)
        self.bgm(name)

    def effect(self, name):
        if self.enabled and name in self.sounds:
            try:
                self.sounds[name].play()
            except (pygame.error, OSError) as error:
                del self.sounds[name]
                LOGGER.warning('効果音 %s を再生できません: %s', name, error)

    def close(self):
        self.closed = True
        if self.enabled:
            self.enabled = False
            try:
                pygame.mixer.music.stop()
                pygame.mixer.stop()
            except pygame.error as error:
                LOGGER.warning('音声の終了時にデバイスを使用できません: %s', error)


class GameAudio:
    def __init__(self, output=None):
        self.output = output if output is not None else MixerAudio()
        self.phase = None
        self.race_key = None
        self.card_key = None
        self.tick = None
        self.positions = self.facing = self.fallen = self.status = None
        self.step_delay = 0.
        self.session_id = None
        self.revision = -1
        self.health_elapsed = 0.

    def update(self, state, model, dt, start_delay=None):
        if not state or state.get('revision', -1) < 0:
            return
        if state.get('sessionId') != self.session_id:
            self.session_id = state.get('sessionId')
            self.revision = -1
            self.phase = self.race_key = self.card_key = None
            self.positions = self.facing = self.fallen = self.status = None
        if state['revision'] < self.revision:
            return
        self.revision = state['revision']
        phase = ('race' if self.phase == 'race' and model and model.moving
                 and state['phase'] in ('payout', 'champion') else state['phase'])
        if phase != self.phase:
            previous = self.phase
            self.phase = phase
            self.output.bgm('race' if phase == 'race' else 'waiting')
            if previous and phase == 'payout':
                statuses = list(model.status) if model else [m['status'] for m in state.get('standings', [])]
                if self.status and statuses.count('goal') > self.status.count('goal'):
                    self.output.effect('goal')
                self.output.effect('payout')
            elif previous and phase != 'race':
                self.output.effect('confirm')
        self.health_elapsed += dt
        if self.health_elapsed >= 5.:
            self.health_elapsed = 0.
            if hasattr(self.output, 'recover'):
                self.output.recover('race' if phase == 'race' else 'waiting')
        if phase != 'race' or model is None:
            self.race_key = None
            return
        key = state['raceIndex']
        if key != self.race_key:
            self.race_key = key
            self.card_key = (key, state['revealed'])
            self.positions = list(model.visual_positions)
            self.facing = list(model.facing)
            self.fallen = list(model.fallen)
            self.status = list(model.status)
            self.tick = None
            self.step_delay = 0.
            if start_delay is None and state['revealed'] == 0:
                self.output.effect('countdown')
        if start_delay is not None and start_delay > 0:
            tick = max(0, ceil(start_delay - .5))
            if tick != self.tick:
                self.output.effect('tick' if tick else 'go')
                self.tick = tick
        card_key = (key, state['revealed'])
        if card_key != self.card_key:
            self.card_key = card_key
            self.output.effect('card')
        # カード集合中は座標・向きの効果音を先走らせない。
        if getattr(model, 'revealing', False):
            return
        facing, fallen, status = list(model.facing), list(model.fallen), list(model.status)
        if any(a != b for a, b in zip(self.facing, facing)):
            self.output.effect('reverse')
        if any(not a and b for a, b in zip(self.fallen, fallen)):
            self.output.effect('tumble')
        if any(a != 'goal' and b == 'goal' for a, b in zip(self.status, status)):
            self.output.effect('goal')
        positions = list(model.visual_positions)
        self.step_delay = max(0., self.step_delay - dt)
        if self.step_delay == 0 and any(abs(a-b) > .001 for a, b in zip(self.positions, positions)):
            self.output.effect('step')
            self.step_delay = .18
        self.positions, self.facing, self.fallen, self.status = positions, facing, fallen, status

    def close(self):
        self.output.close()

    def draw_credit(self, surface):
        if not hasattr(self, 'credit'):
            font = pygame.font.Font(None, 16)
            self.credit = font.render('Race music: Run Amok / Kevin MacLeod (incompetech.com) / CC BY 4.0 - creativecommons.org/licenses/by/4.0/', True, (190, 205, 218))
        pygame.draw.rect(surface, (8, 20, 31), (0, 704, 1280, 16))
        surface.blit(self.credit, (12, 705))
        status = getattr(self.output, 'status', '')
        if status:
            if not hasattr(self, 'status_font'):
                from .app import japanese_font
                self.status_font = pygame.font.Font(japanese_font(None), 20)
            label = self.status_font.render(status, True, (223, 191, 134))
            pygame.draw.rect(surface, (8, 20, 31), (0, 679, 1280, 25))
            surface.blit(label, label.get_rect(center=(640, 691)))
