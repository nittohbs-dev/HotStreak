"""実サーバーのデータを既存Phone状態クラスで読む。ブラウザやネットワークは使わない。"""
import json
from pathlib import Path
from random import Random
import subprocess
from hotstreak_core.state import GameSession, Player
from hotstreak_sync.server import build_app

ROOT = Path(__file__).resolve().parents[2]


def test_actual_game_snapshots_are_accepted_by_every_phone_screen():
    runtime = build_app().state.runtime
    s = GameSession('contract', [Player(str(i), name=f'参加者{i}') for i in range(3)], rng=Random(3))
    runtime.add_session(s)
    samples = []
    def record():
        if s.phase != 'setup-cards':
            for player in s.players:
                samples.append(dict(playerId=player.player_id, snapshot=runtime.snapshot(s, player.player_id)))
    def advance():
        old = s.phase
        runtime.services[old].advance(s)
        runtime.complete_transition(s, old)
    record()
    advance()
    advance()
    for _ in range(3):
        betting = runtime.services['betting']
        record()
        for pid in betting.order(s):
            ticket = next(t for t in betting.stock(s) if t['remaining'])
            betting.act(s, 'picks', dict(ticket, face='safe'), pid)
            record()
        if s.race_index == 3:
            for p in s.players:
                betting.act(s, 'double', {'ticketInstanceId': p.tickets[0]['ticketInstanceId']}, p.player_id)
            record()
        advance()
        record()
        for p in s.players:
            runtime.services['card-seed'].act(s, 'seed', {'handCardId': p.hand[0].instance_id}, p.player_id)
        record()
        advance()
        record()
        for _ in range(150):
            advance()
            record()
            if s.phase == 'payout':
                break
        assert s.phase == 'payout'
        advance()
    script = r'''
const assert = require('node:assert/strict');
const fs = require('node:fs');
const modules = {
  lobby: ['lobby-state.js', 'LobbyScreenState'],
  betting: ['betting-state.js', 'BettingScreenState'],
  'card-seed': ['card-seed-state.js', 'CardSeedScreenState'],
  race: ['race-state.js', 'RaceScreenState'],
  payout: ['payout-state.js', 'PayoutScreenState'],
};
const samples = JSON.parse(fs.readFileSync(0, 'utf8'));
for (const { playerId, snapshot } of samples) {
  const [file, name] = modules[snapshot.phase];
  const Type = require('./src/hotstreak_phone/' + file)[name];
  const state = new Type(playerId);
  if (snapshot.phase === 'lobby') state.playerId = playerId;
  assert.equal(state.applyState(snapshot), true, snapshot.phase + ': ' + state.error);
  assert.equal(state.error, '');
}
console.log(samples.length + ' live phone snapshots accepted');
'''
    result = subprocess.run(['node', '-e', script], cwd=ROOT, input=json.dumps(samples), text=True, capture_output=True)
    assert result.returncode == 0, result.stderr
