"""REQ-play-004: 進行役の固定と会場Enter中継の境界。"""
from random import Random
from uuid import uuid4
from fastapi.testclient import TestClient
from hotstreak_core.session import GameSession
from hotstreak_sync.app import create_app


def setup():
    app = create_app(lambda: GameSession(rng=Random(3)))
    display = TestClient(app)
    created = display.post('/api/sessions').json()
    base = '/api/sessions/' + created['sessionId']
    first, other = TestClient(app), TestClient(app)
    pid = first.post(base+'/join').json()['playerId']
    other.post(base+'/join')
    room = app.state.rooms[created['sessionId']]
    return app, display, first, other, base, room, pid, created['displayToken']


def race(s):
    s.advance()
    s.advance()
    while s.turn < len(s.order):
        key = next(k for k, used in s.stock.items() if used < 3)
        s.pick(s.order[s.turn], dict(ticketId=key, ticketKind='mascot' if key in ('blue','orange','salmon','yellow') else 'side', face='safe'))
    s.advance()
    for p in s.players:
        if p.seed is None:
            s.seed(p.player_id, p.hand[0].instance_id)
    s.advance()


def poll(display, base, token, s, **overrides):
    return display.post(base+'/enter/poll', headers={'X-Display-Token': token}, json=dict(
        revision=s.revision, control=dict(canTap=True, canHold=True, autoRunning=False, notice='ENTERで1枚', **overrides)))


def enter(phone, base, s, action='tap', key=None):
    return phone.post(base+'/enter', headers={'Idempotency-Key': key or str(uuid4())},
                      json=dict(revision=s.revision, phase=s.phase, action=action))


def test_only_first_player_can_enter_and_no_authentication_leaks():
    _, display, first, other, base, room, pid, token = setup()
    assert enter(other, base, room.session).status_code == 403
    assert enter(display, base, room.session).status_code == 403
    assert enter(first, base, room.session).json()['phase'] == 'setup-cards'
    assert first.post(base+'/join').json()['playerId'] == pid
    assert other.post(base+'/enter/poll', json={}).status_code == 403
    assert 'displayToken' not in first.get(base).json()


def test_race_enter_is_once_only_relay_and_does_not_reveal_directly():
    _, display, first, other, base, room, _, token = setup()
    s = room.session
    race(s)
    before = s.snapshot()['revealed']
    assert enter(first, base, s).status_code == 409  # 会場未接続。
    assert poll(display, base, token, s).status_code == 200
    assert enter(other, base, s).status_code == 403
    body = dict(revision=s.revision, phase=s.phase, action='hold')
    headers = {'Idempotency-Key': 'repeat'}
    a = first.post(base+'/enter', json=body, headers=headers)
    assert a.status_code == 200
    assert 'remoteEnter' not in a.json()
    assert first.post(base+'/enter', json=body, headers=headers).json() == a.json()
    assert s.snapshot()['revealed'] == before
    received = poll(display, base, token, s).json()
    assert received['remoteEnter']['action'] == 'hold'
    assert received['remoteEnter']['revision'] == s.revision
    assert 'remoteEnter' not in poll(display, base, token, s).json()


def test_pending_or_expired_or_stale_enter_is_not_replayed():
    _, display, first, _, base, room, _, token = setup()
    s = room.session
    race(s)
    poll(display, base, token, s)
    assert enter(first, base, s).status_code == 200
    # 新しい状態でも未配信入力を上書きしない。
    room.control_revision = s.revision
    assert enter(first, base, s).status_code == 409
    room.enter_command['created'] -= 4
    assert 'remoteEnter' not in poll(display, base, token, s).json()
    assert enter(first, base, s).status_code == 200
    s.revision += 1  # 物理Enterなどが先に進めた状態。
    assert 'remoteEnter' not in poll(display, base, token, s).json()
    room.display_seen -= 4
    assert enter(first, base, s).status_code == 409


def test_start_countdown_disables_remote_enter_and_bad_action_is_rejected():
    _, display, first, _, base, room, _, token = setup()
    s = room.session
    race(s)
    display.post(base+'/enter/poll', headers={'X-Display-Token': token}, json=dict(revision=s.revision,
        control=dict(canTap=False, canHold=False, autoRunning=False, notice='開始準備中')))
    assert enter(first, base, s).status_code == 409
    assert enter(first, base, s, 'anything').status_code == 400


def test_running_enter_records_stop_intent_instead_of_toggle():
    _, display, first, _, base, room, _, token = setup()
    s = room.session
    race(s)
    display.post(base+'/enter/poll', headers={'X-Display-Token': token}, json=dict(revision=s.revision,
        control=dict(canTap=True, canHold=True, autoRunning=True, notice='自動進行中')))
    assert enter(first, base, s).status_code == 200
    assert poll(display, base, token, s).json()['remoteEnter']['action'] == 'stop'
