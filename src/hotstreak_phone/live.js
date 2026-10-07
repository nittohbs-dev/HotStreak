/* 実セッション用の通信。描画は既存モックと同じ State / View を使う。 */
(function () {
  const params = new URLSearchParams(location.search);
  const session = params.get('session');
  const enabled = Boolean(session && params.get('connection') === 'session' && params.get('demo') !== '1');
  window.HotStreakSessionLive = { enabled, start };

  function start(page) {
    const base = `/api/sessions/${encodeURIComponent(session)}`;
    const storageKey = `hotstreak-player-${session}`;
    let playerId = sessionStorage.getItem(storageKey) || '';
    let state, view, ws, timer, stopped = false, revision = -1, busy = false;
    const render = () => view.render(state);
    const error = (message) => {
      state.pending = false;
      state.error = message;
      render();
    };
    const redirect = (phase) => {
      const target = { lobby: 'lobby', 'setup-cards': 'lobby', betting: 'betting',
        'card-seed': 'card-seed', race: 'race', payout: 'payout' }[phase];
      if (target && target !== page) {
        stopped = true;
        if (ws) ws.close();
        location.replace(`${target}.html?${new URLSearchParams({ session, connection: "session" })}`);
        return true;
      }
      return false;
    };
    const receive = (snapshot) => {
      if (snapshot.revision < revision || redirect(snapshot.phase)) return;
      revision = snapshot.revision;
      if (snapshot.viewerPlayerId) {
        playerId = snapshot.viewerPlayerId;
        sessionStorage.setItem(storageKey, playerId);
        state.myPlayerId = playerId;
        if (page === 'lobby') state.playerId = playerId;
      }
      if (page === 'lobby') {
        if (snapshot.phase === 'setup-cards') {
          state.handleMessage('lobby.advanced', snapshot);
        } else {
          state.playerId = playerId;
          state.applyState(snapshot);
        }
      } else {
        state.applyState(snapshot);
      }
      render();
    };
    async function fetchState() {
      const res = await fetch(base, { cache: 'no-store' });
      const data = await res.json();
      if (!res.ok) throw new Error(data.message || '状態を取得できません');
      receive(data);
    }
    async function send(method, suffix, body) {
      if (!body || busy || !state.connected) return;
      busy = true;
      if (state.markPending) state.markPending();
      render();
      // 自動再送しない。応答喪失時はスナップショットで確定状態を確認。
      try {
        const requestId = Array.from(crypto.getRandomValues(new Uint8Array(16)), x => x.toString(16).padStart(2, '0')).join('');
        const res = await fetch(base+suffix, { method, headers: {
          'Content-Type': 'application/json', 'Idempotency-Key': requestId }, body: JSON.stringify(body) });
        const data = await res.json();
        if (!res.ok) throw new Error(data.message || '操作できません');
        receive(data);
      } catch (e) {
        try { await fetchState(); } catch (_) { state.connected = false; }
        error(e.message);
      } finally { busy = false; }
    }
    if (page === 'lobby') {
      state = new HotStreakLobbyState.LobbyScreenState();
      view = new HotStreakLobbyView.LobbyView({
        onNameInput: value => { state.setDraftName(value); render(); },
        onConfirm: () => send('PUT', `/players/${encodeURIComponent(playerId)}/name`, state.buildNameRequest()),
      });
    } else if (page === 'betting') {
      state = new HotStreakBettingState.BettingScreenState(playerId);
      view = new HotStreakBettingView.BettingView({
        onSelect: id => { state.selectTicket(id); render(); },
        onToggleFace: () => { state.toggleFace(); render(); },
        onConfirm: () => send('POST', '/betting/picks', state.buildPickRequest()),
        onDouble: id => send('PUT', '/betting/double', state.buildDoubleRequest(id)),
      });
    } else if (page === 'card-seed') {
      state = new HotStreakCardSeedState.CardSeedScreenState(playerId);
      view = new HotStreakCardSeedView.CardSeedView({
        onSelect: id => { state.selectCard(id); render(); },
        onConfirm: () => send('POST', '/seed', state.buildSeedRequest()),
      });
    } else if (page === 'race') {
      state = new HotStreakRaceState.RaceScreenState(playerId);
      view = new HotStreakRaceView.RaceView({
        onOpenSheet: () => { state.openSheet(); render(); },
        onCloseSheet: () => { state.closeSheet(); render(); },
      });
    } else {
      state = new HotStreakPayoutState.PayoutScreenState(playerId);
      view = new HotStreakPayoutView.PayoutView();
    }
    render();
    async function connect() {
      if (stopped) return;
      try {
        if (page === 'lobby') {
          const res = await fetch(base+'/join', { method: 'POST' });
          const data = await res.json();
          if (!res.ok) {
            await fetchState();
            if (!stopped && data.message) error(data.message);
          } else {
            playerId = data.playerId;
            sessionStorage.setItem(storageKey, playerId);
            state.playerId = playerId;
            receive(data);
          }
        }
        if (stopped) return;
        ws = new WebSocket(`${location.protocol === 'https:' ? 'wss:' : 'ws:'}//${location.host}/ws/sessions/${encodeURIComponent(session)}`);
        ws.onmessage = event => {
          try { receive(JSON.parse(event.data).payload); } catch (_) { error('受信データを確認できません'); }
        };
        ws.onopen = () => fetchState().catch(e => error(e.message));
        ws.onerror = () => ws.close();
        ws.onclose = () => {
          if (stopped) return;
          state.connected = false;
          error('接続が切れました。再接続しています…');
          timer = setTimeout(connect, 1000);
        };
      } catch (e) {
        error(e.message);
        timer = setTimeout(connect, 1000);
      }
    }
    window.addEventListener('beforeunload', () => { stopped = true; clearTimeout(timer); if (ws) ws.close(); });
    connect();
  }
})();
