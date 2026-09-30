"""実RESTを使い、3〜8人がQR参加から3レース・次の受付まで完走する。"""
from random import Random
from uuid import uuid4
import pytest
from fastapi.testclient import TestClient
from hotstreak_sync.server import build_app


@pytest.mark.parametrize('count', range(3, 9))
def test_full_three_races(count):
    app = build_app()
    with TestClient(app) as display:
        created = display.post('/api/sessions', json={}).json()
        sid = created['sessionId']
        base = f'/api/sessions/{sid}'
        session = app.state.runtime.get(sid)
        session.rng = Random(count)
        players = [TestClient(app) for _ in range(count)]
        ids = [p.post(base+'/join').json()['playerId'] for p in players]
        for i, p in enumerate(players):
            assert p.put(base+f'/players/{ids[i]}/name', json={'displayName': f'P{i}'}).status_code == 200
        cookies = {pid: p.cookies.get(f'hs_{sid}') for pid, p in zip(ids, players)}

        def state():
            return display.get(base).json()

        def advance(extra=None):
            current = state()
            body = dict(phase=current['phase'], revision=current['revision'], **(extra or {}))
            headers = {'X-Display-Token': created['displayToken'], 'Idempotency-Key': str(uuid4())}
            result = display.post(base+'/advance', json=body, headers=headers)
            assert result.status_code == 200, result.text
            assert display.post(base+'/advance', json=body, headers=headers).json() == result.json()
            return result.json()

        assert advance({'firstPlayerId': ids[1]})['phase'] == 'betting'
        for race in range(1, 4):
            assert state()['currentPlayerId'] == ids[(1+race-1) % count]
            for turn in range(count*2):
                current = state()
                pid = current['currentPlayerId']
                player = players[ids.index(pid)]
                ticket = next(t for t in current['stock'] if t['remaining'])
                body = dict(ticketKind=ticket['ticketKind'], ticketId=ticket['ticketId'], face='risky' if turn % 2 else 'safe')
                key = {'Idempotency-Key': str(uuid4())}
                result = player.post(base+'/betting/picks', json=body, headers=key)
                assert result.status_code == 200, result.text
                assert player.post(base+'/betting/picks', json=body, headers=key).json() == result.json()
            if race == 3:
                current = state()
                for pid, p in zip(ids, players):
                    ticket = current['picksByPlayer'][pid][0]['ticketInstanceId']
                    assert p.put(base+'/betting/double', json={'ticketInstanceId': ticket}, headers={'Idempotency-Key': str(uuid4())}).status_code == 200
            assert advance()['phase'] == 'card-seed'
            assert 'hand' not in state()
            # 進捗WSには本人接続でも手札・仕込み中身を出さない。
            with players[0].websocket_connect(f'/ws/sessions/{sid}') as ws:
                assert 'hand' not in ws.receive_json()['payload']
                for p in players:
                    hand = p.get(base+'/seed').json()['hand']
                    assert len(hand) == 3
                    result = p.post(base+'/seed', json={'handCardId': hand[0]['cardId']}, headers={'Idempotency-Key': str(uuid4())})
                    assert result.status_code == 200, result.text
                    assert len(result.json()['hand']) == 2
                    event = ws.receive_json()
                    assert 'hand' not in event['payload'] and 'seededCard' not in event['payload']
            assert advance()['phase'] == 'race'
            for _ in range(500):
                result = advance()
                if result['phase'] == 'payout':
                    break
            else:
                pytest.fail('レースが終了しません')
            for pid, p in zip(ids, players):
                personal = p.get(base+'/payout').json()
                assert personal['myBreakdown']['playerId'] == pid
                assert len(personal['myBreakdown']['items']) == 2
            assert len(state()['standings']) == 4
            assert all(1 <= m['rank'] <= 4 for m in state()['standings'])  # 同時DQの同順位を許す。
            assert all(p['balance'] >= 0 for p in state()['balances'])
            next_state = advance()
            assert next_state['phase'] == ('lobby' if race == 3 else 'betting')
        assert next_state['players'] == []
        assert all(token not in str(next_state) for token in cookies.values())
        assert players[0].post(base+'/join').status_code == 200


def test_player_auth_pending_steps_and_seed_privacy():
    app = build_app()
    with TestClient(app) as display:
        created = display.post('/api/sessions', json={}).json()
        sid = created['sessionId']
        base = f'/api/sessions/{sid}'
        players = [TestClient(app) for _ in range(3)]
        ids = [p.post(base+'/join').json()['playerId'] for p in players]
        for i, p in enumerate(players):
            p.put(base+f'/players/{ids[i]}/name', json={'displayName': f'P{i}'})
        def advance():
            state = display.get(base).json()
            return display.post(base+'/advance', json={'phase': state['phase'], 'revision': state['revision']},
                                headers={'X-Display-Token': created['displayToken'], 'Idempotency-Key': str(uuid4())})
        assert advance().status_code == 200
        assert advance().status_code == 409  # 未取得を自動補完しない。
        body = {'ticketKind': 'mascot', 'ticketId': 'blue', 'face': 'safe'}
        assert display.post(base+'/betting/picks', json=body, headers={'Idempotency-Key': 'anonymous'}).status_code == 403
        assert players[1].post(base+'/betting/picks', json=dict(body, playerId=ids[0]), headers={'Idempotency-Key': 'spoof'}).status_code == 403
        assert players[1].post(base+'/betting/picks', json=body, headers={'Idempotency-Key': 'out-of-turn'}).status_code == 403
        for _ in range(6):
            state = display.get(base).json()
            p = players[ids.index(state['currentPlayerId'])]
            ticket = next(t for t in state['stock'] if t['remaining'])
            assert p.post(base+'/betting/picks', json=dict(ticket, face='safe'), headers={'Idempotency-Key': str(uuid4())}).status_code == 200
        assert advance().status_code == 200
        assert advance().status_code == 409  # 未仕込みを自動補完しない。
        hands = [p.get(base+'/seed').json()['hand'] for p in players]
        foreign = hands[1][0]['cardId']
        assert players[0].post(base+'/seed', json={'handCardId': foreign}, headers={'Idempotency-Key': 'foreign'}).status_code == 400
        assert foreign not in str(players[0].get(base+'/seed').json())
        own = hands[0][0]['cardId']
        body = {'handCardId': own}
        key = {'Idempotency-Key': 'own'}
        first = players[0].post(base+'/seed', json=body, headers=key)
        assert first.status_code == 200
        assert players[0].post(base+'/seed', json=body, headers=key).json() == first.json()
        assert players[0].post(base+'/seed', json=body, headers={'Idempotency-Key': 'different'}).status_code == 409
        assert len(players[0].get(base+'/seed').json()['hand']) == 2
        assert own not in str(players[1].get(base+'/seed').json())
