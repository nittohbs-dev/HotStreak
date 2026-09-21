/* CMP-lobby-011（名前入力）・CMP-lobby-012（参加者一覧）。サーバ由来の文字列は textContent でのみ入れる。 */
(function (root, factory) {
  const api = factory();
  if (typeof module === "object" && module.exports) module.exports = api;
  else root.HotStreakLobbyView = api;
})(typeof globalThis !== "undefined" ? globalThis : this, function () {
  function el(tag, className, text) {
    const node = document.createElement(tag);
    if (className) node.className = className;
    if (text !== undefined) node.textContent = text;
    return node;
  }

  class LobbyView {
    constructor(handlers) {
      this.handlers = handlers;
      this.nodes = {
        nameInput: document.getElementById("name-input"),
        summary: document.getElementById("player-count"),
        list: document.getElementById("player-list"),
        confirm: document.getElementById("confirm-button"),
        notice: document.getElementById("notice"),
        hint: document.getElementById("foot-hint"),
      };
      this.nodes.confirm.addEventListener("click", () => this.handlers.onConfirm());
      this.nodes.nameInput.addEventListener("input", (event) => this.handlers.onNameInput(event.target.value));
    }

    render(state) {
      this.renderInput(state);
      this.renderRoster(state);
      this.renderFooter(state);
    }

    /* CMP-lobby-011: 確定後は名前変更 API が無いので入力を閉じる。 */
    renderInput(state) {
      const input = this.nodes.nameInput;
      if (input.value !== state.draftName) input.value = state.draftName;
      input.disabled = state.isNameReady || state.advanced || !state.connected;
    }

    /* CMP-lobby-012 */
    renderRoster(state) {
      this.nodes.summary.textContent = state.connected ? `参加者 ${state.playerCount} 人` : "";
      const list = this.nodes.list;
      list.replaceChildren();
      for (const player of state.players) {
        const row = el("li", "player");
        row.dataset.self = String(player.playerId === state.playerId);
        const label = player.nameReady ? player.displayName : "（入力中）";
        const name = el("span", "player-name", label);
        if (player.playerId === state.playerId) name.append(el("span", "player-self", "（自分）"));
        row.append(name);
        row.append(el("span", "player-status", player.nameReady ? "入力済" : "入力中"));
        list.append(row);
      }
    }

    renderFooter(state) {
      const confirm = this.nodes.confirm;
      confirm.disabled = !state.canSubmit;
      confirm.hidden = state.advanced;
      confirm.textContent = state.pending ? "送信中…" : "この名前で決定";

      let notice = state.error;
      if (!notice && state.handoff) notice = "マ券ドラフトへ移動します…";
      else if (!notice && state.autoNamed && state.me) {
        notice = `名前は「${state.me.displayName}」で決まりました。公開カードの準備中です。`;
      } else if (!notice && state.advanced) notice = "公開カードの準備中です。そのままお待ちください。";
      else if (!notice && !state.connected) notice = "参加しています…";
      else if (!notice && state.allReady) notice = "全員そろいました。次へ進むのを待っています。";
      else if (!notice && state.isNameReady) notice = "ほかの人の入力を待っています。";
      this.nodes.notice.textContent = notice || "";
      this.nodes.notice.dataset.error = String(Boolean(state.error));

      this.nodes.hint.hidden = state.advanced;
    }
  }

  return { LobbyView };
});
