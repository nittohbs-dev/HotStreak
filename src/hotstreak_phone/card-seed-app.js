/* SCR-phone-003 の起動。モック専用で通信はしない（接続は両側のモック完成後）。 */
(function () {
  const playerId = HotStreakCardSeedMock.MOCK_PLAYER_ID;
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

  const driver = new HotStreakCardSeedMock.MockDriver(receive);
  const label = document.getElementById("demo-scene");
  document.getElementById("demo-bar").hidden = false;
  document.getElementById("demo-next").addEventListener("click", () => {
    label.textContent = driver.next();
  });
  label.textContent = driver.sceneName;

  view.render(state);
  driver.start();
})();
