/* SCR-phone-002 の起動。URL パラメータで接続先と playerId を受ける（lobby 未実装のための暫定）。 */
(function () {
  const params = new URLSearchParams(location.search);
  const isDemo = params.get("demo") === "1";
  const server = params.get("server") || "http://127.0.0.1:8000";
  const sessionId = params.get("session") || "";
  const notice = document.getElementById("notice");

  function fail(message) {
    document.getElementById("turn-status").textContent = "接続できません";
    notice.textContent = message;
    notice.dataset.error = "true";
  }

  if (!isDemo && (!sessionId || !params.get("player"))) {
    fail("session と player を URL に付けて開いてください。例: betting.html?session=S1&player=p1（お試しは betting.html?demo=1）");
    return;
  }

  const playerId = isDemo ? HotStreakBettingDemo.DEMO_PLAYER_ID : params.get("player");
  const state = new HotStreakBettingState.BettingScreenState(playerId);

  let driver;
  const receive = (kind, payload) => {
    state.handleMessage(kind, payload);
    view.render(state);
  };

  const view = new HotStreakBettingView.BettingView({
    onSelect: (ticketId) => {
      state.selectTicket(ticketId);
      view.render(state);
    },
    onToggleFace: () => {
      state.toggleFace();
      view.render(state);
    },
    onConfirm: () => {
      const request = state.buildPickRequest();
      if (!request) return;
      state.markPending();
      view.render(state);
      driver.sendPick(request);
    },
    onDouble: (ticketInstanceId) => {
      const request = state.buildDoubleRequest(ticketInstanceId);
      if (!request) return;
      state.markPending();
      view.render(state);
      driver.sendDouble(request);
    },
  });

  if (isDemo) {
    driver = new HotStreakBettingDemo.DemoDriver(receive);
    const bar = document.getElementById("demo-bar");
    const label = document.getElementById("demo-scene");
    const button = document.getElementById("demo-next");
    bar.hidden = false;
    button.addEventListener("click", () => {
      label.textContent = driver.next();
    });
    label.textContent = driver.sceneName;
  } else {
    try {
      driver = new HotStreakBettingConnection.BettingConnection({ server, sessionId, playerId, onMessage: receive });
    } catch (error) {
      fail(error.message);
      return;
    }
  }

  view.render(state);
  driver.start();
  window.addEventListener("beforeunload", () => driver.close());
})();
