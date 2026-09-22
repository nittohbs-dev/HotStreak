/* SCR-phone-004 の起動。モック専用で通信はしない（接続は両側のモック完成後）。 */
(function () {
  const state = new HotStreakRaceState.RaceScreenState(HotStreakRaceMock.MOCK_PLAYER_ID);

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

  const driver = new HotStreakRaceMock.MockDriver(receive);
  const label = document.getElementById("demo-scene");
  document.getElementById("demo-bar").hidden = false;
  document.getElementById("demo-next").addEventListener("click", () => {
    label.textContent = driver.next();
  });
  label.textContent = driver.sceneName;

  view.render(state);
  driver.start();
})();
