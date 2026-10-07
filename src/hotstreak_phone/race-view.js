/* レース中のスマホには、お題と本人が購入したマ券だけを表示する。 */
(function (root, factory) {
  const api = factory();
  if (typeof module === "object" && module.exports) module.exports = api;
  else root.HotStreakRaceView = api;
})(typeof globalThis !== "undefined" ? globalThis : this, function () {
  const FACE_LABEL = { safe: "セーフ", risky: "リスキー" };

  function el(tag, className, text) {
    const node = document.createElement(tag);
    if (className) node.className = className;
    if (text !== undefined) node.textContent = text;
    return node;
  }

  function betChip(bet) {
    const chip = el("li", "bet-chip");
    chip.append(el("span", "bet-label", bet.label));
    chip.append(el("span", `face face-${bet.face}`, FACE_LABEL[bet.face]));
    if (bet.double) chip.append(el("span", "double-mark", "★ダブル"));
    return chip;
  }

  class RaceView {
    constructor() {
      this.nodes = {
        prompt: document.getElementById("side-prompt"),
        event: document.getElementById("race-event"),
        myBets: document.getElementById("my-bets"),
      };
    }

    render(state) {
      this.renderMeta(state);
      this.renderSelf(state);
    }

    renderMeta(state) {
      this.nodes.prompt.textContent = state.prompt ? state.prompt.text : "お題を確認しています…";
    }

    renderSelf(state) {
      const bets = this.nodes.myBets;
      bets.replaceChildren();
      for (const bet of state.myBets) bets.append(betChip(bet));
      if (!state.connected) bets.append(el("li", "bet-chip bet-empty", "確認しています…"));
    }
  }

  return { RaceView };
});
