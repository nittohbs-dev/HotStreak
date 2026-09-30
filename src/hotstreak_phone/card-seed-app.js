/* SCR-phone-003: セッション指定時は実接続。それ以外は従来のデモ。 */
(function () {
  const params = new URLSearchParams(typeof location === "undefined" ? "" : location.search);
  const live = params.has("session") && params.get("demo") !== "1";
  const playerId = live ? params.get("player") : HotStreakCardSeedMock.MOCK_PLAYER_ID;
  const state = new HotStreakCardSeedState.CardSeedScreenState(playerId);

  const receive = (kind, payload) => {
    state.handleMessage(kind, payload);
    view.render(state);
  };

  const view = new HotStreakCardSeedView.CardSeedView({
    onSelect: (cardId) => {
      state.selectCard(cardId);
      view.render(state);
    },
    onConfirm: () => {
      const request = state.buildSeedRequest();
      if (!request) return;
      state.markPending();
      view.render(state);
      driver.sendSeed(request);
    },
  });

  const driver = live ? new HotStreakLive.Connection({
    phase: "card-seed", sessionId: params.get("session"), playerId,
    server: params.get("server") || location.origin, onMessage: receive,
  }) : new HotStreakCardSeedMock.MockDriver(receive);
  if (!live) {
  const label = document.getElementById("demo-scene");
  document.getElementById("demo-bar").hidden = false;
  document.getElementById("demo-next").addEventListener("click", () => {
    label.textContent = driver.next();
  });
  label.textContent = driver.sceneName;
  }

  view.render(state);
  driver.start();
  if (live) window.addEventListener("beforeunload", () => driver.close());
})();
