/* SCR-phone-005: 本人の実精算と3レース終了後の受付復帰。 */
(function () {
  if (typeof HotStreakSessionLive !== "undefined" && HotStreakSessionLive.enabled) { HotStreakSessionLive.start("payout"); return; }
  const params = new URLSearchParams(typeof location === "undefined" ? "" : location.search);
  const live = params.has("session") && params.get("demo") !== "1";
  const playerId = live ? params.get("player") : HotStreakPayoutMock.MOCK_PLAYER_ID;
  const newState = () => new HotStreakPayoutState.PayoutScreenState(playerId);
  let state = newState();
  const view = new HotStreakPayoutView.PayoutView();

  const receive = (kind, payload) => {
    state.handleMessage(kind, payload);
    view.render(state);
  };

  const driver = live ? new HotStreakLive.Connection({
    phase: "payout", sessionId: params.get("session"), playerId,
    server: params.get("server") || location.origin, onMessage: receive,
  }) : new HotStreakPayoutMock.MockDriver(receive);
  if (!live) {
  const label = document.getElementById("demo-scene");
  document.getElementById("demo-bar").hidden = false;
  document.getElementById("demo-next").addEventListener("click", () => {
    /* Enter 後は状態が凍結されるため、最初の場面に戻るときは作り直す。 */
    if (state.advancedTo) state = newState();
    label.textContent = driver.next();
  });
  label.textContent = driver.sceneName;
  }

  view.render(state);
  driver.start();
  if (live) window.addEventListener("beforeunload", () => driver.close());
})();
