/* CLS-payout-011 の状態部。DOM・通信を持たない。SCR-phone-005、REQ-payout-005。
   金額はサーバ（PayoutCalculator）の算出値をそのまま持つ。クライアントでは精算しない。 */
(function (root, factory) {
  const api = factory();
  if (typeof module === "object" && module.exports) module.exports = api;
  else root.HotStreakPayoutState = api;
})(typeof globalThis !== "undefined" ? globalThis : this, function () {
  const FACES = ["safe", "risky"];
  const KINDS = ["mascot", "side"];
  const TIERS = ["top", "mid", "bot"];
  const NEXT_PHASES = ["betting", "lobby"];

  const MESSAGES = {
    invalidState: "配当の情報を確認できません。画面を開き直してください。",
  };

  function isObject(value) {
    return typeof value === "object" && value !== null && !Array.isArray(value);
  }

  function isText(value) {
    return typeof value === "string" && value.length > 0;
  }

  function isRank(value) {
    return Number.isInteger(value) && value >= 1;
  }

  function parseStanding(raw) {
    if (!isObject(raw) || !isText(raw.mascotId) || !isText(raw.displayName)) throw new TypeError("standing");
    if (!isRank(raw.rank)) throw new TypeError("rank");
    return {
      mascotId: raw.mascotId,
      displayName: raw.displayName,
      color: isText(raw.color) ? raw.color : "",
      rank: raw.rank,
      disqualified: raw.disqualified === true,
    };
  }

  function parseBalance(raw) {
    if (!isObject(raw) || !isText(raw.playerId)) throw new TypeError("balance");
    if (!Number.isInteger(raw.balance) || raw.balance < 0) throw new TypeError("balance amount");
    if (!Number.isInteger(raw.delta) || !isRank(raw.rank)) throw new TypeError("balance rank");
    return {
      playerId: raw.playerId,
      displayName: isText(raw.displayName) ? raw.displayName : raw.playerId,
      balance: raw.balance,
      delta: raw.delta,
      rank: raw.rank,
    };
  }

  function parseItem(raw) {
    if (!isObject(raw) || !isText(raw.ticketInstanceId) || !isText(raw.label)) throw new TypeError("item");
    if (!KINDS.includes(raw.kind) || !FACES.includes(raw.face) || !TIERS.includes(raw.tier)) throw new TypeError("item kind");
    if (!Number.isInteger(raw.amount)) throw new TypeError("item amount");
    return {
      ticketInstanceId: raw.ticketInstanceId,
      label: raw.label,
      kind: raw.kind,
      face: raw.face,
      tier: raw.tier,
      double: raw.double === true,
      amount: raw.amount,
    };
  }

  function parseBreakdown(raw, myPlayerId) {
    if (raw === undefined || raw === null) return null;
    if (!isObject(raw) || raw.playerId !== myPlayerId) throw new TypeError("breakdown");
    if (!Number.isInteger(raw.total) || !Array.isArray(raw.items)) throw new TypeError("breakdown total");
    return { total: raw.total, items: raw.items.map(parseItem) };
  }

  class PayoutScreenState {
    constructor(myPlayerId) {
      this.myPlayerId = myPlayerId || "";
      this.connected = false;
      this.advancedTo = "";
      this.error = "";
      this.raceIndex = 0;
      this.standings = [];
      this.balances = [];
      this.breakdown = null;
      this.winners = [];
    }

    get me() {
      return this.balances.find((player) => player.playerId === this.myPlayerId) || null;
    }

    get playerTotal() {
      return this.balances.length;
    }

    get isFinalRace() {
      return this.raceIndex === 3;
    }

    /* 並び順はサーバの rank をそのまま使う（順位付けはクライアントで再現しない）。 */
    get rankedStandings() {
      return this.standings.slice().sort((a, b) => a.rank - b.rank);
    }

    get rankedBalances() {
      return this.balances.slice().sort((a, b) => a.rank - b.rank);
    }

    /* BR-payout-007: 同点最多は共同優勝。勝者はサーバが決める。 */
    isWinner(playerId) {
      return this.isFinalRace && this.winners.includes(playerId);
    }

    /* 受信ペイロードは検証してからまとめて反映する。壊れていれば状態を進めない。 */
    applyState(payload) {
      if (!isObject(payload)) {
        this.error = MESSAGES.invalidState;
        return false;
      }
      let next;
      try {
        if (payload.phase !== "payout") throw new TypeError("phase");
        const raceIndex = payload.raceIndex;
        if (!Number.isInteger(raceIndex) || raceIndex < 1 || raceIndex > 3) throw new TypeError("raceIndex");
        if (!Array.isArray(payload.standings) || !Array.isArray(payload.balances)) throw new TypeError("list");
        const standings = payload.standings.map(parseStanding);
        if (new Set(standings.map((m) => m.mascotId)).size !== standings.length) throw new TypeError("duplicate mascot");
        const balances = payload.balances.map(parseBalance);
        const ids = balances.map((p) => p.playerId);
        if (new Set(ids).size !== ids.length) throw new TypeError("duplicate player");
        const breakdown = parseBreakdown(payload.myBreakdown, this.myPlayerId);
        const winners = payload.winners === undefined ? [] : payload.winners;
        if (!Array.isArray(winners) || !winners.every((id) => ids.includes(id))) throw new TypeError("winners");
        next = { raceIndex, standings, balances, breakdown, winners: winners.slice() };
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
      if (this.advancedTo) return false;
      if (kind === "payout.state") return this.applyState(payload);
      if (kind === "payout.advanced") {
        if (!isObject(payload) || !NEXT_PHASES.includes(payload.phase)) return false;
        this.advancedTo = payload.phase;
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

  return { PayoutScreenState, MESSAGES };
});
