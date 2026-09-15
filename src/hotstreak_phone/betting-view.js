/* CMP-betting-011〜014 の描画。サーバ由来の文字列は textContent でのみ入れる。 */
(function (root, factory) {
  const api = factory(root.HotStreakTicketPayouts);
  if (typeof module === "object" && module.exports) module.exports = api;
  else root.HotStreakBettingView = api;
})(typeof globalThis !== "undefined" ? globalThis : this, function (payouts) {
  const FACE_LABEL = { safe: "セーフ", risky: "リスキー" };

  function el(tag, className, text) {
    const node = document.createElement(tag);
    if (className) node.className = className;
    if (text !== undefined) node.textContent = text;
    return node;
  }

  class BettingView {
    constructor(handlers) {
      this.handlers = handlers;
      this.nodes = {
        turn: document.getElementById("turn-status"),
        turnDetail: document.getElementById("turn-detail"),
        race: document.getElementById("race-meta"),
        prompt: document.getElementById("side-prompt"),
        list: document.getElementById("ticket-list"),
        held: document.getElementById("held-tickets"),
        double: document.getElementById("double-picker"),
        doubleSlots: document.getElementById("double-slots"),
        confirm: document.getElementById("confirm-button"),
        notice: document.getElementById("notice"),
      };
      this.nodes.confirm.addEventListener("click", () => this.handlers.onConfirm());
    }

    render(state) {
      this.renderTurn(state);
      this.renderMeta(state);
      this.renderList(state);
      this.renderHeld(state);
      this.renderDouble(state);
      this.renderFooter(state);
    }

    /* CMP-betting-011 */
    renderTurn(state) {
      const bar = this.nodes.turn;
      if (state.advanced) {
        bar.textContent = "カード仕込みへ進みます";
        bar.dataset.mode = "done";
      } else if (!state.connected) {
        bar.textContent = "接続中…";
        bar.dataset.mode = "offline";
      } else if (state.isMyTurn) {
        bar.textContent = "あなたの番です";
        bar.dataset.mode = "mine";
      } else {
        bar.textContent = state.currentPlayerName ? `${state.currentPlayerName} の番です` : "手番を待っています";
        bar.dataset.mode = "waiting";
      }
      const detail = [];
      if (state.round) detail.push(`${state.round}周目`);
      if (state.turnIndex && state.turnTotal) detail.push(`${state.turnIndex}/${state.turnTotal}`);
      this.nodes.turnDetail.textContent = detail.join(" ");
    }

    renderMeta(state) {
      this.nodes.race.textContent = state.raceIndex ? `レース ${state.raceIndex}/3` : "";
      this.nodes.prompt.textContent = state.prompt ? state.prompt.text : "";
    }

    /* CMP-betting-012 */
    renderList(state) {
      const list = this.nodes.list;
      list.replaceChildren();
      for (const ticket of state.stock) {
        const selected = state.selectedTicketId === ticket.ticketId;
        const face = selected ? state.selectedFace : "safe";
        const soldOut = state.isSoldOut(ticket);

        const row = el("li", "ticket");
        row.dataset.selected = String(selected);
        row.dataset.soldOut = String(soldOut);

        const head = el("div", "ticket-head");
        head.append(el("span", "ticket-label", ticket.label));
        head.append(el("span", `face face-${face}`, FACE_LABEL[face]));
        row.append(head);

        row.append(el("p", "ticket-payout", payouts.summary(ticket.ticketKind, face, ticket.tier)));
        row.append(el("p", "ticket-remaining", soldOut ? "残り 0枚（選べません）" : `残り ${ticket.remaining}枚`));

        if (selected) {
          const flip = el("button", "flip", `裏返す → ${FACE_LABEL[face === "safe" ? "risky" : "safe"]}`);
          flip.type = "button";
          flip.addEventListener("click", (event) => {
            event.stopPropagation();
            this.handlers.onToggleFace();
          });
          row.append(flip);
        }

        if (!soldOut) {
          row.addEventListener("click", () => this.handlers.onSelect(ticket.ticketId));
        }
        list.append(row);
      }
    }

    /* CMP-betting-013: 所持は常に2枠（空き枠を見せる） */
    renderHeld(state) {
      const held = this.nodes.held;
      held.replaceChildren();
      for (let slot = 0; slot < 2; slot += 1) {
        const pick = state.myPicks[slot];
        if (!pick) {
          held.append(el("li", "held held-empty", "空き"));
          continue;
        }
        const item = el("li", "held");
        item.append(el("span", "held-label", pick.label));
        item.append(el("span", `face face-${pick.face}`, FACE_LABEL[pick.face]));
        if (state.myDoubleId === pick.ticketInstanceId) item.append(el("span", "double-mark", "★ダブル"));
        held.append(item);
      }
    }

    /* CMP-betting-014: 第3レースのみ */
    renderDouble(state) {
      const section = this.nodes.double;
      section.hidden = !state.needsDouble;
      if (!state.needsDouble) return;
      const slots = this.nodes.doubleSlots;
      slots.replaceChildren();
      for (const pick of state.myPicks) {
        const button = el("button", "double-option", `${pick.label}（${FACE_LABEL[pick.face]}）`);
        button.type = "button";
        button.disabled = state.pending;
        button.addEventListener("click", () => this.handlers.onDouble(pick.ticketInstanceId));
        slots.append(button);
      }
    }

    renderFooter(state) {
      const confirm = this.nodes.confirm;
      confirm.disabled = !state.canConfirm;
      confirm.textContent = state.pending ? "送信中…" : "この札に投票する";

      let notice = state.error;
      if (!notice && state.advanced) notice = "全員が2枚取得しました。次の画面を待っています。";
      else if (!notice && state.connected && !state.isMyTurn) notice = "ほかの人の番です。操作できません。";
      else if (!notice && state.needsDouble) notice = "配当ダブルにする札を1枚選んでください。";
      else if (!notice && state.isMyTurn && state.heldCount >= 2) notice = "このレースの取得は終わりました。";
      this.nodes.notice.textContent = notice || "";
      this.nodes.notice.dataset.error = String(Boolean(state.error));
    }
  }

  return { BettingView };
});
