/* CMP-race-011 お題・012 マスコット順位・013 自分の札・014 全員状況。サーバ由来の文字列は textContent のみ。 */
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

  function money(amount) {
    return amount < 0 ? `-$${Math.abs(amount)}` : `$${amount}`;
  }

  function betChip(bet) {
    const chip = el("li", "bet-chip");
    chip.append(el("span", "bet-label", bet.label));
    chip.append(el("span", `face face-${bet.face}`, FACE_LABEL[bet.face]));
    if (bet.double) chip.append(el("span", "double-mark", "★ダブル"));
    return chip;
  }

  class RaceView {
    constructor(handlers) {
      this.handlers = handlers;
      this.nodes = {
        prompt: document.getElementById("side-prompt"),
        race: document.getElementById("race-meta"),
        mascots: document.getElementById("mascot-rank"),
        myBets: document.getElementById("my-bets"),
        balance: document.getElementById("my-balance"),
        rank: document.getElementById("my-rank"),
        sheetButton: document.getElementById("sheet-button"),
        sheet: document.getElementById("all-players-sheet"),
        sheetList: document.getElementById("sheet-list"),
        sheetClose: document.getElementById("sheet-close"),
        notice: document.getElementById("notice"),
      };
      this.nodes.sheetButton.addEventListener("click", () => this.handlers.onOpenSheet());
      this.nodes.sheetClose.addEventListener("click", () => this.handlers.onCloseSheet());
    }

    render(state) {
      this.renderMeta(state);
      this.renderMascots(state);
      this.renderSelf(state);
      this.renderSheet(state);
      this.renderNotice(state);
    }

    /* CMP-race-011 */
    renderMeta(state) {
      this.nodes.race.textContent = state.raceIndex ? `レース ${state.raceIndex}/3` : "";
      this.nodes.prompt.textContent = state.prompt ? state.prompt.text : "";
      this.nodes.prompt.hidden = !state.prompt;
    }

    /* CMP-race-012: 順位はサーバの値をそのまま並べる。 */
    renderMascots(state) {
      const list = this.nodes.mascots;
      list.replaceChildren();
      for (const mascot of state.rankedMascots) {
        const item = el("li", "mascot");
        item.dataset.color = mascot.color;
        item.dataset.out = String(mascot.disqualified);
        item.append(el("span", "mascot-rank", `${mascot.rank}位`));
        item.append(el("span", "mascot-name", mascot.displayName));
        if (mascot.disqualified) item.append(el("span", "mascot-note", "失格"));
        else if (mascot.finished) item.append(el("span", "mascot-note", "ゴール"));
        list.append(item);
      }
    }

    /* CMP-race-013 */
    renderSelf(state) {
      const bets = this.nodes.myBets;
      bets.replaceChildren();
      for (const bet of state.myBets) bets.append(betChip(bet));
      if (!state.myBets.length) bets.append(el("li", "bet-chip bet-empty", "マ券なし"));

      const me = state.me;
      this.nodes.balance.textContent = me ? money(me.balance) : "";
      this.nodes.rank.textContent = me ? `${me.rank}位 / ${state.playerTotal}人` : "";
    }

    /* CMP-race-014: SCR-phone-004b */
    renderSheet(state) {
      this.nodes.sheetButton.disabled = !state.connected || state.finished;
      this.nodes.sheet.hidden = !state.sheetOpen;
      if (!state.sheetOpen) return;
      const list = this.nodes.sheetList;
      list.replaceChildren();
      for (const player of state.rankedPlayers) {
        const row = el("li", "sheet-player");
        row.dataset.self = String(player.playerId === state.myPlayerId);
        const name = el("p", "sheet-player-name", player.displayName);
        if (player.playerId === state.myPlayerId) name.append(el("span", "sheet-player-self", "（自分）"));
        row.append(name);
        const chips = el("ul", "bet-list");
        for (const bet of player.bets) chips.append(betChip(bet));
        if (!player.bets.length) chips.append(el("li", "bet-chip bet-empty", "マ券なし"));
        row.append(chips);
        list.append(row);
      }
    }

    renderNotice(state) {
      let notice = state.error;
      if (!notice && state.finished) notice = "レースが終わりました。配当へ進みます。";
      else if (!notice && !state.connected) notice = "レースの開始を待っています…";
      else if (!notice) notice = "会場の画面でレースが進みます。";
      this.nodes.notice.textContent = notice;
      this.nodes.notice.dataset.error = String(Boolean(state.error));
    }
  }

  return { RaceView };
});
