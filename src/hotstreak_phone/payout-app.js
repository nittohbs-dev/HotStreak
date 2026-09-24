/* SCR-phone-005 の起動。モック専用で通信はしない（接続は両側のモック完成後）。 */
(function () {
  const newState = () => new HotStreakPayoutState.PayoutScreenState(HotStreakPayoutMock.MOCK_PLAYER_ID);
  let state = newState();
  const view = new HotStreakPayoutView.PayoutView();

  const receive = (kind, payload) => {
    state.handleMessage(kind, payload);
    view.render(state);
  };

  const driver = new HotStreakPayoutMock.MockDriver(receive);
  const label = document.getElementById("demo-scene");
  document.getElementById("demo-bar").hidden = false;
  document.getElementById("demo-next").addEventListener("click", () => {
    /* Enter 後は状態が凍結されるため、最初の場面に戻るときは作り直す。 */
    if (state.advancedTo) state = newState();
    label.textContent = driver.next();
  });
  label.textContent = driver.sceneName;

  view.render(state);
  driver.start();
})();
