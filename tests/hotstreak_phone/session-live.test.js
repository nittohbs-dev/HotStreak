const test = require('node:test');
const assert = require('node:assert/strict');
const vm = require('node:vm');
const fs = require('node:fs');
const source = fs.readFileSync(require.resolve('../../src/hotstreak_phone/live.js'), 'utf8');

async function phone() {
  const events = {}, documentEvents = {}, intervals = new Map(), sockets = [], redirects = [];
  let snapshot = { phase: 'lobby', revision: 1, playerId: 'p', viewerPlayerId: 'p' };
  let renders = 0, reads = 0;
  class State {
    applyState() { this.connected = true; }
    handleMessage() { this.connected = true; }
  }
  class Socket {
    constructor() { sockets.push(this); }
    close() { if (this.onclose) this.onclose(); }
  }
  const document = { visibilityState: 'visible', addEventListener: (k, fn) => { documentEvents[k] = fn; } };
  const window = { addEventListener: (k, fn) => { events[k] = fn; } };
  vm.runInNewContext(source, {
    window, document, URLSearchParams, AbortController, setTimeout, clearTimeout,
    setInterval: fn => { const id = {}; intervals.set(id, fn); return id; },
    clearInterval: id => intervals.delete(id),
    location: { search: '?session=s&connection=session', protocol: 'http:', host: 'game:8010', replace: url => redirects.push(url) },
    sessionStorage: { getItem: () => 'p', setItem() {} },
    HotStreakLobbyState: { LobbyScreenState: State },
    HotStreakLobbyView: { LobbyView: class { render() { renders++; } } },
    WebSocket: Socket,
    fetch: async () => { reads++; return { ok: true, json: async () => snapshot }; },
  });
  window.HotStreakSessionLive.start('lobby');
  await new Promise(resolve => setImmediate(resolve));
  return { events, documentEvents, document, sockets, redirects, intervals,
    tick: () => [...intervals.values()][0](),
    update: next => { snapshot = next; },
    renders: () => renders, reads: () => reads };
}

test('WS通知が来なくても定期取得で現在フェーズへ移動する', async () => {
  const p = await phone();
  const renders = p.renders();
  await p.tick();
  assert.equal(p.renders(), renders, '同じrevisionでは入力中の表示を再描画しない');
  p.update({ phase: 'betting', revision: 3 });
  await p.tick();
  assert.deepEqual(p.redirects, ['betting.html?session=s&connection=session']);
  p.events.pagehide();
});

test('非表示中は取得せず画面復帰直後に同期する', async () => {
  const p = await phone();
  p.document.visibilityState = 'hidden';
  const reads = p.reads();
  await p.tick();
  assert.equal(p.reads(), reads);
  p.update({ phase: 'race', revision: 5 });
  p.document.visibilityState = 'visible';
  await p.documentEvents.visibilitychange();
  assert.deepEqual(p.redirects, ['race.html?session=s&connection=session']);
  p.events.pagehide();
});

test('ページキャッシュから復帰しても同期とWS接続を再開する', async () => {
  const p = await phone();
  p.events.pagehide();
  assert.equal(p.intervals.size, 0);
  p.events.pageshow({ persisted: true });
  await new Promise(resolve => setImmediate(resolve));
  assert.equal(p.intervals.size, 1);
  assert.equal(p.sockets.length, 2);
  p.update({ phase: 'card-seed', revision: 6 });
  await p.tick();
  assert.deepEqual(p.redirects, ['card-seed.html?session=s&connection=session']);
  p.events.pagehide();
});
