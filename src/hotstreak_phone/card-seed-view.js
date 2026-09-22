/* CMP-seed-011 手札・012 仕込み状況・013 確定ボタン。サーバ由来の文字列は textContent でのみ入れる。 */
(function (root, factory) {
  const api = factory(root.HotStreakCardSprite);
  if (typeof module === "object" && module.exports) module.exports = api;
  else root.HotStreakCardSeedView = api;
})(typeof globalThis !== "undefined" ? globalThis : this, function (sprite) {
  const CARD_SCALE = 0.42;
  const CARD_BACK_RECT = [1440, 2352, 240, 336];

  function el(tag, className, text) {
    const node = document.createElement(tag);
    if (className) node.className = className;
    if (text !== undefined) node.textContent = text;
    return node;
  }

  class CardSeedView {
    constructor(handlers) {
      this.handlers = handlers;
      this.nodes = {
        meta: document.getElementById("seed-meta"),
        progress: document.getElementById("seed-progress"),
        hand: document.getElementById("hand-list"),
        seededSlot: document.getElementById("seeded-slot"),
        status: document.getElementById("status-list"),
        confirm: document.getElementById("confirm-button"),
        notice: document.getElementById("notice"),
        hint: document.getElementById("foot-hint"),
      };
      this.nodes.confirm.addEventListener("click", () => this.handlers.onConfirm());
    }

    render(state) {
      this.renderMeta(state);
      this.renderHand(state);
      this.renderSeeded(state);
      this.renderStatus(state);
      this.renderFooter(state);
    }

    renderMeta(state) {
      const meta = [];
      if (state.raceIndex) meta.push(`レース ${state.raceIndex}/3`);
      meta.push(`手札 ${state.handCount}枚`);
      this.nodes.meta.textContent = meta.join(" ・ ");
      this.nodes.progress.textContent = state.playerTotal
        ? `仕込み ${state.seededCount} / ${state.playerTotal} 人`
        : "";
    }

    /* CMP-seed-011 */
    renderHand(state) {
      const list = this.nodes.hand;
      list.replaceChildren();
      for (const card of state.hand) {
        const selected = state.selectedCardId === card.cardId;
        const item = el("li", "hand-card");
        item.dataset.selected = String(selected);
        item.dataset.locked = String(state.seeded);
        item.append(sprite.cardArt(card.rect, CARD_SCALE));
        item.append(el("p", "hand-label", card.label));
        if (state.canSelect(card.cardId)) {
          item.addEventListener("click", () => this.handlers.onSelect(card.cardId));
        }
        list.append(item);
      }
    }

    /* BR-seed-004: 仕込んだ札は裏向き。中身は出さない。 */
    renderSeeded(state) {
      const slot = this.nodes.seededSlot;
      slot.hidden = !state.seeded;
      if (!state.seeded) return;
      slot.replaceChildren();
      slot.append(sprite.cardArt(CARD_BACK_RECT, CARD_SCALE));
      slot.append(el("p", "hand-label", "仕込み済み"));
    }

    /* CMP-seed-012 */
    renderStatus(state) {
      const list = this.nodes.status;
      list.replaceChildren();
      for (const entry of state.progress) {
        const isSelf = entry.playerId === state.myPlayerId;
        const row = el("li", "seed-player");
        row.dataset.self = String(isSelf);
        const name = el("span", "seed-player-name", entry.displayName);
        if (isSelf) name.append(el("span", "seed-player-self", "（自分）"));
        row.append(name);
        let label = entry.seeded ? "済" : "未";
        if (isSelf && !entry.seeded) label = state.selectedCardId ? "選択中" : "未";
        row.append(el("span", "seed-player-status", label));
        list.append(row);
      }
    }

    renderFooter(state) {
      const confirm = this.nodes.confirm;
      confirm.disabled = !state.canConfirm;
      confirm.hidden = state.seeded || state.advanced;
      confirm.textContent = state.pending ? "送信中…" : "このカードを仕込む";

      let notice = state.error;
      if (!notice && state.advanced) notice = "レースがまもなく始まります。そのままお待ちください。";
      else if (!notice && state.allSeeded) notice = `全員そろいました。レース用カード束 ${state.deckCountExpected} 枚。`;
      else if (!notice && state.seeded) notice = "ほかの人の仕込みを待っています。仕込んだカードは変更できません。";
      else if (!notice && !state.selectedCardId) notice = "仕込むカードを1枚選んでください。";
      this.nodes.notice.textContent = notice || "";
      this.nodes.notice.dataset.error = String(Boolean(state.error));

      this.nodes.hint.hidden = state.advanced;
    }
  }

  return { CardSeedView, CARD_SCALE, CARD_BACK_RECT };
});
