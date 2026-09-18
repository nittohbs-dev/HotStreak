/* SCR-phone-001 の起動。QR の URL は設計上 /join/{sessionId} だが、静的配信のため session を URL パラメータで受ける。 */
(function () {
  const params = new URLSearchParams(location.search);
  const isDemo = params.get("demo") === "1";
  const server = params.get("server") || "http://127.0.0.1:8000";
  const sessionId = params.get("session") || "";
  const notice = document.getElementById("notice");

  function fail(message) {
    notice.textContent = message;
    notice.dataset.error = "true";
    document.getElementById("confirm-button").disabled = true;
  }

  if (!isDemo && !sessionId) {
    fail("session を URL に付けて開いてください。例: lobby.html?session=S1（お試しは lobby.html?demo=1）");
    return;
  }

  const state = new HotStreakLobbyState.LobbyScreenState();

  let driver;
  const receive = (kind, payload) => {
    state.handleMessage(kind, payload);
    view.render(state);
    if (state.handoff) handOffToBetting();
  };

  function handOffToBetting() {
    driver.close();
    if (isDemo) {
      location.assign("betting.html?demo=1");
      return;
    }
    const next = new URLSearchParams({ server, session: sessionId, player: state.playerId || "" });
    location.assign(`betting.html?${next.toString()}`);
  }

  const view = new HotStreakLobbyView.LobbyView({
    onNameInput: (text) => {
      state.setDraftName(text);
      view.render(state);
    },
    onConfirm: () => {
      const request = state.buildNameRequest();
      if (!request) return;
      state.markPending();
      view.render(state);
      driver.sendName(request);
    },
  });

  if (isDemo) {
    driver = new HotStreakLobbyDemo.DemoDriver(receive);
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
      driver = new HotStreakLobbyConnection.LobbyConnection({ server, sessionId, onMessage: receive });
    } catch (error) {
      fail(error.message);
      return;
    }
  }

  view.render(state);
  driver.start();
  window.addEventListener("beforeunload", () => driver.close());
})();
