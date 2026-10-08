"""実HTTPセッションと会場Displayを実時間で動かし、画面とミキサー出力を記録する。

PYTHONPATH=src uv run --python 3.12 --with-requirements requirements.txt \
  --with imageio-ffmpeg python scripts/record-audio-preview.py --output /absolute/output
"""
import argparse
from array import array
import json
import math
import socket
import subprocess
import threading
import time
import wave
from http.cookiejar import CookieJar
from pathlib import Path
from random import Random
from urllib.request import HTTPCookieProcessor, Request, build_opener
from uuid import uuid4

import imageio_ffmpeg
import pygame
from pygame._sdl2.mixer import set_post_mix
import uvicorn
from hotstreak_core.session import GameSession
from hotstreak_sync.app import create_app
from hotstreak_display.live import Application, Connection
from hotstreak_display.audio import GameAudio, MixerAudio


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--seed', type=int, default=37)
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=True)
    with socket.socket() as sock:
        sock.bind(('127.0.0.1', 0))
        port = sock.getsockname()[1]
    origin = f'http://127.0.0.1:{port}'
    server = uvicorn.Server(uvicorn.Config(
        create_app(lambda: GameSession(rng=Random(args.seed))),
        host='127.0.0.1', port=port, log_level='error'))
    thread = threading.Thread(target=server.run, daemon=True)
    thread.start()
    deadline = time.monotonic() + 10
    while not server.started:
        if time.monotonic() > deadline:
            raise RuntimeError('録画用サーバを起動できません')
        time.sleep(.02)
    http = build_opener(HTTPCookieProcessor(CookieJar()))

    def request(path, data=None, method=None):
        headers = {'Content-Type': 'application/json', 'Idempotency-Key': str(uuid4())}
        req = Request(origin+path, data=json.dumps(data).encode() if data is not None else None,
                      headers=headers, method=method)
        with http.open(req, timeout=5) as response:
            return json.load(response)

    credentials = request('/api/sessions', {})
    base = '/api/sessions/'+credentials['sessionId']
    player = request(base+'/join', {})['playerId']
    request(base+'/players/'+player+'/name', {'displayName': 'サウンド確認'}, 'PUT')
    pygame.mixer.pre_init(44100, -16, 2, 512)
    pygame.init()
    display = pygame.display.set_mode((1280, 720))
    pygame.display.set_caption('HotStreak — 音付き動作確認')
    canvas = pygame.Surface((1280, 720))
    audio_events, chunks, chunk_times = [], [], []
    start = time.monotonic()

    class LoggedMixer(MixerAudio):
        def bgm(self, name):
            if name != self.music:
                audio_events.append(dict(time=time.monotonic()-start, kind='bgm', name=name))
            super().bgm(name)
            # music.play()後に登録。旧フックの解放が新フックを消さないよう先に外す。
            set_post_mix(None)
            set_post_mix(postmix)

        def effect(self, name):
            audio_events.append(dict(time=time.monotonic()-start, kind='effect', name=name))
            super().effect(name)

    output = LoggedMixer()
    if not output.enabled:
        raise RuntimeError('音声出力が無効のため録画を中止します')
    app = Application(audio=GameAudio(output))
    connection = Connection(origin, credentials)
    connection.thread.start()
    ffmpeg = imageio_ffmpeg.get_ffmpeg_exe()
    silent = args.output/'capture-video.mp4'
    error_log = (args.output/'encoder.log').open('w')
    encoder = subprocess.Popen([ffmpeg, '-y', '-loglevel', 'warning', '-f', 'rawvideo',
        '-pixel_format', 'rgb24', '-video_size', '1280x720', '-framerate', '30', '-i', '-',
        '-an', '-c:v', 'libx264', '-preset', 'ultrafast', '-crf', '20', '-pix_fmt', 'yuv420p',
        str(silent)], stdin=subprocess.PIPE, stderr=error_log)

    def postmix(_processor, data):
        if not chunks:
            chunk_times.append(time.monotonic())
        chunks.append(bytes(data))

    clock = pygame.time.Clock()
    phase = None
    phase_since = last_player_action = 0.
    released = False
    auto_started = False
    frame_count = 0
    phases = []
    start = time.monotonic()
    set_post_mix(postmix)
    try:
        while time.monotonic()-start < 160:
            dt = clock.tick(30)/1000
            now = time.monotonic()-start
            while not connection.messages.empty():
                kind, payload = connection.messages.get_nowait()
                if kind in ('state', 'advanced'):
                    app.receive(payload, advanced=kind == 'advanced')
                else:
                    raise RuntimeError(str(payload))
            # 録画専用ウィンドウの終了操作は尊重する。
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    raise RuntimeError('録画を中断しました')
            state = app.state
            if state:
                visible = 'race' if app.moving else state['phase']
                if visible != phase:
                    phase, phase_since = visible, now
                    phases.append(dict(phase=phase, time=now))
                    print(f'{now:.1f}s {phase}', flush=True)
                age = now-phase_since
                if state['phase'] == 'betting' and age > 1 and now-last_player_action > 1:
                    if state['currentPlayerId'] == player:
                        ticket = next(t for t in state['stock'] if t['remaining'] > 0)
                        request(base+'/betting/picks', dict(ticketId=ticket['ticketId'],
                            ticketKind=ticket['ticketKind'], face='safe'))
                        last_player_action = now
                if state['phase'] == 'card-seed' and age > 1:
                    personal = request(base)
                    if personal['seededCard'] is None:
                        request(base+'/seed', {'handCardId': personal['hand'][0]['cardId']})
                ready = state['phase'] in ('lobby', 'setup-cards') or (
                    state['phase'] == 'betting' and state['currentPlayerId'] is None) or (
                    state['phase'] == 'card-seed' and all(p['seeded'] for p in state['progress']))
                if ready and age > (7 if phase == 'lobby' else 4) and not app.pending:
                    app.handle_event(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_RETURN))
                    app.handle_event(pygame.event.Event(pygame.KEYUP, key=pygame.K_RETURN))
                if state['phase'] == 'race' and app.start_delay <= 0 and not auto_started:
                    app.handle_event(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_RETURN))
                    auto_started = True
                if auto_started and app.auto_running and not released:
                    app.handle_event(pygame.event.Event(pygame.KEYUP, key=pygame.K_RETURN))
                    released = True
            app.update(dt)
            command = app.take_command()
            if command:
                connection.commands.put(command)
            app.draw(canvas, origin+'/join/'+credentials['sessionId'])
            display.blit(canvas, (0, 0))
            pygame.display.flip()
            data = pygame.image.tobytes(canvas, 'RGB')
            # エンコーダ待ちがあっても映像の時刻を実時間に合わせる。
            target = max(1, round((time.monotonic()-start)*30))
            while frame_count < target:
                encoder.stdin.write(data)
                frame_count += 1
            if state and phase in ('lobby', 'race', 'payout'):
                image = args.output/(phase+'.png')
                if not image.exists() and now-phase_since > 2:
                    pygame.image.save(canvas, image)
            if phase == 'payout' and now-phase_since > 6:
                break
        else:
            raise RuntimeError('配当まで完了しませんでした')
    finally:
        set_post_mix(None)
        audio_format = pygame.mixer.get_init()
        app.audio.close()
        connection.stop.set()
        connection.thread.join(timeout=5)
        encoder.stdin.close()
        encoder.wait(timeout=30)
        error_log.close()
        pygame.quit()
        server.should_exit = True
        thread.join(timeout=5)
    if encoder.returncode:
        raise RuntimeError('映像エンコード失敗')
    pcm = b''.join(chunks)
    rate, bits, channels = audio_format
    assert bits == -16 and channels == 2
    audio_seconds = len(pcm)/(rate*channels*2)
    if abs(audio_seconds-frame_count/30) > .5 or not any(pcm):
        raise RuntimeError(f'録音の長さ・音声を確認してください: audio={audio_seconds:.3f}s video={frame_count/30:.3f}s')
    audio_file = args.output/'capture-mixer.wav'
    with wave.open(str(audio_file), 'wb') as w:
        w.setnchannels(channels)
        w.setsampwidth(2)
        w.setframerate(rate)
        w.writeframes(pcm)
    first_chunk_duration = len(chunks[0])/(rate*channels*2)
    offset = max(0., chunk_times[0]-start-first_chunk_duration)
    movie = args.output/'HotStreak-audio-preview.mp4'
    subprocess.run([ffmpeg, '-y', '-loglevel', 'warning', '-i', str(silent),
        '-itsoffset', str(offset), '-i', str(audio_file), '-map', '0:v:0', '-map', '1:a:0',
        '-c:v', 'copy', '-c:a', 'aac', '-b:a', '192k', '-af', 'apad',
        '-t', str(frame_count/30), '-movflags', '+faststart', str(movie)], check=True)
    samples = array('h', pcm)
    peak = max(abs(sample) for sample in samples)
    clipped = sum(sample in (-32768, 32767) for sample in samples)
    rms = math.sqrt(sum(sample*sample for sample in samples)/len(samples))/32768
    if not rms or clipped:
        raise RuntimeError(f'録音が無音またはクリップしています: rms={rms}, clipped={clipped}')
    checked = subprocess.run([ffmpeg, '-v', 'error', '-i', str(movie), '-f', 'null', '-'],
                             capture_output=True, text=True)
    if checked.returncode or checked.stderr:
        raise RuntimeError('動画の全体デコードに失敗: '+checked.stderr)
    metadata = dict(seed=args.seed, fps=30, frames=frame_count, seconds=frame_count/30,
        audioSeconds=len(pcm)/(rate*channels*2), audioOffset=offset,
        audioPeak=peak/32768, audioRms=rms, clippedSamples=clipped, fullDecode=True,
        recording='Live Pygame frames and SDL post-mix audio; real-time HTTP session; automated participant and Enter inputs.',
        phases=phases, audioEvents=audio_events, result=app.state['phase'])
    (args.output/'capture.json').write_text(json.dumps(metadata, ensure_ascii=False, indent=2))
    print(str(movie), flush=True)


if __name__ == '__main__':
    main()
