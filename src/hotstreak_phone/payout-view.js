/* CMP-payout-010 配当画面・011 着順要約・012 個人内訳・013 所持金順位。サーバ由来の文字列は textContent のみ。 */
(function (root, factory) {
  const payouts = typeof module === "object" && module.exports ? require("./ticket-payouts.js") : root.HotStreakTicketPayouts;
  const api = factory(payouts);
  if (typeof module === "object" && module.exports) module.exports = api;
  else root.HotStreakPayoutView = api;
})(typeof globalThis !== "undefined" ? globalThis : this, function (payouts) {
  const FACE_LABEL = { safe: "セーフ", risky: "リスキー" };
  const NEXT_NOTICE = {
    betting: "次のレースのマ券ドラフトへ進みます。",
    lobby: "試合が終わりました。ロビーに戻ります。",
  };

  function el(tag, className, text) {
    const node = document.createElement(tag);
    if (className) node.className = className;
    if (text !== undefined) node.textContent = text;
    return node;
  }

  /* 増減は符号を付けて見せる（+$3 / -$5 / $0）。 */
  function signed(amount) {
    return amount > 0 ? `+${payouts.money(amount)}` : payouts.money(amount);
  }

  class PayoutView {
    constructor() {
      this.nodes = {
        title: document.getElementById("payout-title"),
        standings: document.getElementById("standing-list"),
        total: document.getElementById("my-total"),
        breakdown: document.getElementById("breakdown-list"),
        balances: document.getElementById("balance-list"),
        notice: document.getElementById("notice"),
      };
    }

    render(state) {
      this.renderTitle(state);
      this.renderStandings(state);
      this.renderBreakdown(state);
      this.renderBalances(state);
      this.renderNotice(state);
    }

    /* CMP-payout-010 */
    renderTitle(state) {
      this.nodes.title.textContent = state.raceIndex ? `レース${state.raceIndex} 結果` : "配当";
    }

    /* CMP-payout-011: 順位はサーバの値をそのまま並べる。 */
    renderStandings(state) {
      const list = this.nodes.standings;
      list.replaceChildren();
      for (const mascot of state.rankedStandings) {
        const item = el("li", "standing");
        item.dataset.color = mascot.color;
        item.dataset.out = String(mascot.disqualified);
        item.append(el("span", "standing-rank", `${mascot.rank}位`));
        item.append(el("span", "standing-name", mascot.displayName));
        if (mascot.disqualified) item.append(el("span", "standing-note", "失格"));
        list.append(item);
      }
    }

    /* CMP-payout-012: ダブル札は倍にした後の額（マイナスも倍）をサーバから受け取る。 */
    renderBreakdown(state) {
      const breakdown = state.breakdown;
      this.nodes.total.textContent = breakdown ? signed(breakdown.total) : "";
      this.nodes.total.dataset.sign = breakdown ? String(Math.sign(breakdown.total)) : "0";

      const list = this.nodes.breakdown;
      list.replaceChildren();
      if (!breakdown || !breakdown.items.length) {
        if (state.connected) list.append(el("li", "breakdown-row breakdown-empty", "マ券なし"));
        return;
      }
      for (const item of breakdown.items) {
        const row = el("li", "breakdown-row");
        row.dataset.double = String(item.double);
        const name = el("span", "breakdown-name");
        name.append(el("span", "bet-label", item.label));
        name.append(el("span", `face face-${item.face}`, FACE_LABEL[item.face]));
        if (item.double) name.append(el("span", "double-mark", "★ダブル ×2"));
        row.append(name);
        const amount = el("span", "breakdown-amount", signed(item.amount));
        amount.dataset.sign = String(Math.sign(item.amount));
        row.append(amount);
        list.append(row);
      }
    }

    /* CMP-payout-013: 自分を強調。レース3は優勝（同点なら共同優勝）を付ける。 */
    renderBalances(state) {
      const list = this.nodes.balances;
      list.replaceChildren();
      const winnerLabel = state.winners.length > 1 ? "共同優勝" : "優勝";
      for (const player of state.rankedBalances) {
        const self = player.playerId === state.myPlayerId;
        const row = el("li", "balance-row");
        row.dataset.self = String(self);
        row.dataset.winner = String(state.isWinner(player.playerId));
        row.append(el("span", "balance-rank", `${player.rank}位`));
        const name = el("span", "balance-name", player.displayName);
        if (self) name.append(el("span", "balance-self", "（自分）"));
        if (state.isWinner(player.playerId)) name.append(el("span", "winner-mark", winnerLabel));
        row.append(name);
        row.append(el("span", "balance-money", payouts.money(player.balance)));
        const delta = el("span", "balance-delta", signed(player.delta));
        delta.dataset.sign = String(Math.sign(player.delta));
        row.append(delta);
        list.append(row);
      }
    }

    renderNotice(state) {
      let notice = state.error;
      if (!notice && state.advancedTo) notice = NEXT_NOTICE[state.advancedTo];
      else if (!notice && !state.connected) notice = "配当を集計しています…";
      else if (!notice) notice = state.isFinalRace ? "ラズパイ Enter でロビーへ" : "ラズパイ Enter で次のレースへ";
      this.nodes.notice.textContent = notice;
      this.nodes.notice.dataset.error = String(Boolean(state.error));
    }
  }

  return { PayoutView };
});
