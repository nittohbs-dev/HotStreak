/* CLS-race-011 の状態部。DOM・通信を持たない。SCR-phone-004 / 004b、REQ-race-005, 006。 */
(function (root, factory) {
  const api = factory();
  if (typeof module === "object" && module.exports) module.exports = api;
  else root.HotStreakRaceState = api;
})(typeof globalThis !== "undefined" ? globalThis : this, function () {
  const FACES = ["safe", "risky"];

  const MESSAGES = {
    invalidState: "レースの情報を確認できません。画面を開き直してください。",
  };

  function isObject(value) {
    return typeof value === "object" && value !== null && !Array.isArray(value);
  }

  function isText(value) {
    return typeof value === "string" && value.length > 0;
  }

  function parseMascot(raw) {
    if (!isObject(raw) || !isText(raw.mascotId) || !isText(raw.displayName)) throw new TypeError("mascot");
    if (!Number.isInteger(raw.rank) || raw.rank < 1) throw new TypeError("rank");
    return {
      mascotId: raw.mascotId,
      displayName: raw.displayName,
      color: isText(raw.color) ? raw.color : "",
      rank: raw.rank,
      disqualified: raw.disqualified === true,
      finished: raw.finished === true,
    };
  }

  function parseBet(raw) {
    if (!isObject(raw) || !isText(raw.ticketInstanceId) || !isText(raw.label)) throw new TypeError("bet");
    if (!FACES.includes(raw.face)) throw new TypeError("face");
    return {
      ticketInstanceId: raw.ticketInstanceId,
      label: raw.label,
      face: raw.face,
      double: raw.double === true,
    };
  }

  function parsePlayer(raw) {
    if (!isObject(raw) || !isText(raw.playerId) || !Number.isInteger(raw.balance)) throw new TypeError("player");
    if (!Number.isInteger(raw.rank) || raw.rank < 1) throw new TypeError("player rank");
    return {
      playerId: raw.playerId,
      displayName: isText(raw.displayName) ? raw.displayName : raw.playerId,
      balance: raw.balance,
      rank: raw.rank,
      bets: Array.isArray(raw.bets) ? raw.bets.map(parseBet) : [],
    };
  }

  class RaceScreenState {
    constructor(myPlayerId) {
      this.myPlayerId = myPlayerId || "";
      this.connected = false;
      this.finished = false;
      this.error = "";
      this.raceIndex = 0;
      this.prompt = null;
      this.mascots = [];
      this.players = [];
      this.sheetOpen = false;
    }

    get me() {
      return this.players.find((player) => player.playerId === this.myPlayerId) || null;
    }

    get myBets() {
      return this.me ? this.me.bets : [];
    }

    get playerTotal() {
      return this.players.length;
    }

    /* 並び順はサーバの rank をそのまま使う（順位付けはクライアントで再現しない）。 */
    get rankedMascots() {
      return this.mascots.slice().sort((a, b) => a.rank - b.rank);
    }

    get rankedPlayers() {
      return this.players.slice().sort((a, b) => a.rank - b.rank);
    }

    openSheet() {
      if (this.finished || !this.connected) return false;
      this.sheetOpen = true;
      return true;
    }

    closeSheet() {
      this.sheetOpen = false;
      return true;
    }

    /* 受信ペイロードは検証してからまとめて反映する。壊れていれば状態を進めない。 */
    applyState(payload) {
      if (!isObject(payload)) {
        this.error = MESSAGES.invalidState;
        return false;
      }
      let next;
      try {
        if (payload.phase !== "race") throw new TypeError("phase");
        const raceIndex = payload.raceIndex;
        if (!Number.isInteger(raceIndex) || raceIndex < 1 || raceIndex > 3) throw new TypeError("raceIndex");
        if (!Array.isArray(payload.mascots) || !Array.isArray(payload.players)) throw new TypeError("list");
        const mascots = payload.mascots.map(parseMascot);
        if (new Set(mascots.map((m) => m.mascotId)).size !== mascots.length) throw new TypeError("duplicate mascot");
        const players = payload.players.map(parsePlayer);
        if (new Set(players.map((p) => p.playerId)).size !== players.length) throw new TypeError("duplicate player");
        const prompt = isObject(payload.prompt) && isText(payload.prompt.text) ? { text: payload.prompt.text } : null;
        next = { raceIndex, mascots, players, prompt };
      } catch (error) {
        this.error = MESSAGES.invalidState;
        return false;
      }

      Object.assign(this, next);
      this.connected = true;
      this.error = "";
      return true;
    }

    handleMessage(kind, payload) {
      if (this.finished) return false;
      if (kind === "race.state") return this.applyState(payload);
      if (kind === "race.finished") {
        if (!isObject(payload) || payload.phase !== "payout") return false;
        this.finished = true;
        this.sheetOpen = false;
        this.error = "";
        return true;
      }
      if (kind === "error") {
        this.error = isObject(payload) && isText(payload.message) ? payload.message : MESSAGES.invalidState;
        return true;
      }
      return false;
    }
  }

  return { RaceScreenState, MESSAGES };
});
