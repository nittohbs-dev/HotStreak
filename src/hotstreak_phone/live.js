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
    let refreshTimer, refreshing = false;
    let latestSnapshot;
    const hostControls = document.getElementById('host-controls');
    const hostButton = document.getElementById('host-advance');
    const hostReason = document.getElementById('host-reason');
    const render = () => {
      view.render(state);
      if (!hostControls || !latestSnapshot) return;
      const host = Boolean(latestSnapshot.viewerPlayerId && latestSnapshot.viewerPlayerId === latestSnapshot.hostPlayerId);
      hostControls.hidden = !host || latestSnapshot.phase === 'race';
      hostButton.textContent = busy ? '進行中…' : (latestSnapshot.advanceLabel || '次へ');
      hostButton.disabled = busy || !state.connected || !latestSnapshot.canAdvance;
      hostReason.textContent = !state.connected ? '再接続しています…' : (latestSnapshot.advanceReason || 'あなたが進行役です');
    };
    if (hostButton) hostButton.addEventListener('click', () => {
      if (!latestSnapshot || hostButton.disabled) return;
      send('POST', '/advance', { revision: latestSnapshot.revision, phase: latestSnapshot.phase });
    });
    const error = (message) => {
      state.pending = false;
      state.error = message;
      render();
    };
    const redirect = (phase) => {
      const target = { lobby: 'lobby', 'setup-cards': 'lobby', betting: 'betting',
        'card-seed': 'card-seed', race: 'race', payout: 'payout', champion: 'payout' }[phase];
      if (target && target !== page) {
        stopped = true;
        if (ws) ws.close();
        location.replace(`${target}.html?${new URLSearchParams({ session, connection: "session" })}`);
        return true;
      }
      return false;
    };
    const receive = (snapshot) => {
      if (stopped || snapshot.revision < revision || redirect(snapshot.phase)) return;
      latestSnapshot = snapshot;
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
    async function fetchState(onlyChanged = false) {
      const controller = new AbortController();
      const timeout = setTimeout(() => controller.abort(), 5000);
      try {
        const res = await fetch(base, { cache: 'no-store', signal: controller.signal });
        const data = await res.json();
        if (!res.ok) throw new Error(data.message || '状態を取得できません');
        // 定期確認で未確定の札選択や入力を上書きしない。
        if (!onlyChanged || data.revision > revision || !state.connected) receive(data);
      } finally { clearTimeout(timeout); }
    }
    async function refresh() {
      if (stopped || refreshing || busy || document.visibilityState === 'hidden') return;
      refreshing = true;
      try { await fetchState(true); }
      catch (_) { /* WebSocketの再接続を妨げず、次の確認で復旧する。 */ }
      finally { refreshing = false; }
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
      } finally { busy = false; if (!stopped) render(); }
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
    // Safariでは画面復帰後もWebSocketがOPENのまま通知が止まることがある。
    // 通知とは別に本人の最新状態を確認し、手動再読込を不要にする。
    const startRefresh = () => {
      clearInterval(refreshTimer);
      refreshTimer = setInterval(refresh, 2000);
    };
    document.addEventListener('visibilitychange', refresh);
    window.addEventListener('online', refresh);
    window.addEventListener('pagehide', () => {
      stopped = true;
      clearTimeout(timer);
      clearInterval(refreshTimer);
      if (ws) ws.close();
    });
    window.addEventListener('pageshow', event => {
      if (!event.persisted) return;
      stopped = false;
      startRefresh();
      refresh();
      connect();
    });
    startRefresh();
    connect();
  }
})();
