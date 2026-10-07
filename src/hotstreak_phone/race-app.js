/* SCR-phone-004: セッション指定時は会場と同じレースを購読する。 */
(function () {
  if (typeof HotStreakSessionLive !== "undefined" && HotStreakSessionLive.enabled) { HotStreakSessionLive.start("race"); return; }
  const params = new URLSearchParams(typeof location === "undefined" ? "" : location.search);
  const live = params.has("session") && params.get("demo") !== "1";
  const playerId = live ? params.get("player") : HotStreakRaceMock.MOCK_PLAYER_ID;
  const state = new HotStreakRaceState.RaceScreenState(playerId);

  const receive = (kind, payload) => {
    state.handleMessage(kind, payload);
    view.render(state);
  };

  const view = new HotStreakRaceView.RaceView({
    onOpenSheet: () => {
      state.openSheet();
      view.render(state);
    },
    onCloseSheet: () => {
      state.closeSheet();
      view.render(state);
    },
  });

  const driver = live ? new HotStreakLive.Connection({
    phase: "race", sessionId: params.get("session"), playerId,
    server: params.get("server") || location.origin, onMessage: receive,
  }) : new HotStreakRaceMock.MockDriver(receive);
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
