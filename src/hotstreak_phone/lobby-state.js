/* CLS-lobby-011 の状態部。DOM・通信を持たない。SCR-phone-001 / REQ-lobby-002〜006。 */
(function (root, factory) {
  const api = factory();
  if (typeof module === "object" && module.exports) module.exports = api;
  else root.HotStreakLobbyState = api;
})(typeof globalThis !== "undefined" ? globalThis : this, function () {
  const MIN_PLAYERS = 3;
  const MAX_PLAYERS = 8;

  const MESSAGES = {
    invalidState: "参加者の情報を確認できません。再接続してください。",
    disconnected: "接続が切れました。再接続しています…",
  };

  function isObject(value) {
    return typeof value === "object" && value !== null && !Array.isArray(value);
  }

  function isText(value) {
    return typeof value === "string" && value.length > 0;
  }

  function parsePlayer(raw) {
    if (!isObject(raw) || !isText(raw.playerId)) throw new TypeError("player");
    if (typeof raw.displayName !== "string" || typeof raw.nameReady !== "boolean") throw new TypeError("player name");
    if (raw.nameReady && raw.displayName === "") throw new TypeError("name ready");
    return { playerId: raw.playerId, displayName: raw.displayName, nameReady: raw.nameReady };
  }

  class LobbyScreenState {
    constructor() {
      this.playerId = null;
      this.connected = false;
      this.pending = false;
      this.error = "";
      this.players = [];
      this.draftName = "";
      this.advanced = false;
      this.handoff = false;
      this.autoNamed = false;
    }

    get me() {
      return this.players.find((player) => player.playerId === this.playerId) || null;
    }

    get isNameReady() {
      return Boolean(this.me && this.me.nameReady);
    }

    get playerCount() {
      return this.players.length;
    }

    /* BR-lobby-007: 3人未満では進行しないので揃い扱いにしない。 */
    get allReady() {
      return this.playerCount >= MIN_PLAYERS && this.players.every((player) => player.nameReady);
    }

    get trimmedName() {
      return this.draftName.trim();
    }

    /* 空名はサーバへ送らずクライアントで止める（api.md 400 相当）。 */
    get canSubmit() {
      return Boolean(
        this.connected && !this.pending && !this.advanced && !this.isNameReady && this.playerId && this.trimmedName
      );
    }

    setDraftName(text) {
      if (this.isNameReady || this.advanced) return false;
      this.draftName = typeof text === "string" ? text : "";
      return true;
    }

    buildNameRequest() {
      if (!this.canSubmit) return null;
      return { displayName: this.trimmedName };
    }

    markPending() {
      this.pending = true;
      this.error = "";
    }

    applyState(payload) {
      if (!isObject(payload)) {
        this.error = MESSAGES.invalidState;
        return false;
      }
      let players;
      try {
        if (payload.phase !== "lobby") throw new TypeError("phase");
        if (!Array.isArray(payload.players)) throw new TypeError("players");
        players = payload.players.map(parsePlayer);
        if (players.length > MAX_PLAYERS) throw new TypeError("player count");
        if (new Set(players.map((player) => player.playerId)).size !== players.length) {
          throw new TypeError("duplicate player");
        }
      } catch (error) {
        this.error = MESSAGES.invalidState;
        return false;
      }

      this.players = players;
      this.connected = true;
      this.pending = false;
      this.error = "";
      // 確定済みの名前はサーバの値を正とし、入力欄の下書きを残さない。
      if (this.isNameReady) this.draftName = this.me.displayName;
      return true;
    }

    /* 進行後は phase が lobby でなくなるため、名簿だけ取り込む（REQ-lobby-007 の自動命名を映す）。 */
    refreshRoster(payload) {
      if (!isObject(payload) || !Array.isArray(payload.players)) return false;
      let players;
      try {
        players = payload.players.map(parsePlayer);
      } catch (error) {
        return false;
      }
      const wasNameReady = this.isNameReady;
      this.players = players;
      if (this.isNameReady) {
        this.draftName = this.me.displayName;
        if (!wasNameReady) this.autoNamed = true;
      }
      return true;
    }

    handleMessage(kind, payload) {
      if (this.handoff) return false;
      if (kind === "joined") {
        if (!isObject(payload) || !isText(payload.playerId)) {
          this.error = MESSAGES.invalidState;
          return false;
        }
        this.playerId = payload.playerId;
        return this.applyState(payload);
      }
      if (kind === "lobby.state") return this.advanced ? this.refreshRoster(payload) : this.applyState(payload);
      if (kind === "lobby.advanced") {
        if (this.advanced || !isObject(payload) || payload.phase !== "setup-cards") return false;
        this.advanced = true;
        this.pending = false;
        this.error = "";
        this.refreshRoster(payload);
        return true;
      }
      if (kind === "setup.advanced") {
        if (!isObject(payload) || payload.phase !== "betting") return false;
        this.advanced = true;
        this.handoff = true;
        return true;
      }
      if (kind === "disconnected") {
        this.connected = false;
        this.pending = false;
        this.error = MESSAGES.disconnected;
        return true;
      }
      if (kind === "error") {
        this.pending = false;
        this.error = isObject(payload) && isText(payload.message) ? payload.message : MESSAGES.invalidState;
        return true;
      }
      return false;
    }
  }

  return { LobbyScreenState, MESSAGES, MIN_PLAYERS, MAX_PLAYERS };
});
