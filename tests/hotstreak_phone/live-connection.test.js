const test = require('node:test');
const assert = require('node:assert/strict');
const { Connection } = require('../../src/hotstreak_phone/live-connection.js');

function driver(phase = 'card-seed') {
  const events = [], urls = [];
  global.location = { origin: 'http://game:8000', assign: url => urls.push(url) };
  const c = new Connection({ phase, sessionId: 's', playerId: 'p', onMessage: (...event) => events.push(event) });
  c.online = true;
  return { c, events, urls };
}

test('仕込みのWS後は本人認証付きGETで手札を更新する', async () => {
  const { c, events } = driver();
  global.fetch = async (url, options) => {
    assert.equal(options.credentials, 'same-origin');
    return { ok: true, json: async () => ({ phase: 'card-seed', revision: 2, playerId: 'p', hand: [{ cardId: 'blue:1' }] }) };
  };
  await c.refresh();
  assert.equal(events[0][0], 'seed.state');
  assert.equal(events[0][1].hand[0].cardId, 'blue:1');
});

test('再接続時に進行済みなら現在の画面へ遷移する', async () => {
  const { c, urls } = driver('betting');
  global.fetch = async () => ({ ok: true, json: async () => ({ phase: 'race', revision: 7, playerId: 'p' }) });
  await c.refresh();
  assert.equal(urls[0], 'race.html?session=s&player=p');
  assert.equal(c.closed, true);
});

test('応答消失後に同じ操作を再送しても操作IDを変更しない', async () => {
  const { c } = driver('betting');
  const keys = [];
  global.fetch = async (url, options) => {
    if (options.method === 'GET') return { ok: true, json: async () => ({ phase: 'betting', revision: 4, playerId: 'p' }) };
    keys.push(options.headers['Idempotency-Key']);
    if (keys.length === 1) throw new TypeError('network failed after commit');
    return { ok: true, json: async () => ({}) };
  };
  const body = { ticketId: 'blue', ticketKind: 'mascot', face: 'safe' };
  assert.equal(await c.sendPick(body), false);
  assert.equal(await c.sendPick(body), true);
  assert.equal(keys.length, 2);
  assert.equal(keys[0], keys[1]);
});
