/* CLS-betting-011 の状態部。DOM・通信を持たない。SCR-phone-002 / REQ-betting-001〜006。 */
(function (root, factory) {
  const api = factory();
  if (typeof module === "object" && module.exports) module.exports = api;
  else root.HotStreakBettingState = api;
})(typeof globalThis !== "undefined" ? globalThis : this, function () {
  const TICKET_KINDS = ["mascot", "side"];
  const TIERS = ["top", "mid", "bot"];
  const FACES = ["safe", "risky"];
  const HELD_MAX = 2;
  const DOUBLE_RACE = 3;

  const MESSAGES = {
    invalidState: "ベット状況を確認できません。再接続してください。",
    disconnected: "接続が切れました。再接続しています…",
  };

  function isObject(value) {
    return typeof value === "object" && value !== null && !Array.isArray(value);
  }

  function isText(value) {
    return typeof value === "string" && value.length > 0;
  }

  function isCount(value) {
    return Number.isInteger(value) && value >= 0;
  }

  function parseTicket(raw) {
    if (!isObject(raw)) throw new TypeError("ticket");
    const ticket = {
      ticketId: raw.ticketId,
      ticketKind: raw.ticketKind,
      label: raw.label,
      tier: raw.tier,
      remaining: raw.remaining,
    };
    if (!isText(ticket.ticketId) || !isText(ticket.label)) throw new TypeError("ticket id");
    if (!TICKET_KINDS.includes(ticket.ticketKind)) throw new TypeError("ticket kind");
    if (!TIERS.includes(ticket.tier)) throw new TypeError("ticket tier");
    if (!isCount(ticket.remaining)) throw new TypeError("ticket remaining");
    return ticket;
  }

  function parsePick(raw) {
    if (!isObject(raw)) throw new TypeError("pick");
    const pick = {
      ticketInstanceId: raw.ticketInstanceId,
      ticketId: raw.ticketId,
      ticketKind: raw.ticketKind,
      label: raw.label,
      tier: raw.tier,
      face: raw.face,
    };
    if (!isText(pick.ticketInstanceId) || !isText(pick.ticketId)) throw new TypeError("pick id");
    if (!TICKET_KINDS.includes(pick.ticketKind)) throw new TypeError("pick kind");
    if (!TIERS.includes(pick.tier)) throw new TypeError("pick tier");
    if (!FACES.includes(pick.face)) throw new TypeError("pick face");
    if (!isText(pick.label)) pick.label = pick.ticketId;
    return pick;
  }

  function parsePlayer(raw) {
    if (!isObject(raw) || !isText(raw.playerId)) throw new TypeError("player");
    return {
      playerId: raw.playerId,
      displayName: isText(raw.displayName) ? raw.displayName : raw.playerId,
    };
  }

  class BettingScreenState {
    constructor(myPlayerId) {
      this.myPlayerId = myPlayerId || "";
      this.connected = false;
      this.advanced = false;
      this.pending = false;
      this.error = "";
      this.raceIndex = 0;
      this.round = 0;
      this.turnIndex = 0;
      this.turnTotal = 0;
      this.currentPlayerId = null;
      this.stock = [];
      this.players = [];
      this.myPicks = [];
      this.myDoubleId = null;
      this.selectedTicketId = null;
      this.selectedFace = null;
    }

    get isMyTurn() {
      return this.connected && !this.advanced && this.currentPlayerId === this.myPlayerId;
    }

    get heldCount() {
      return this.myPicks.length;
    }

    get isDoubleRace() {
      return this.raceIndex === DOUBLE_RACE;
    }

    /* BR-betting-006: レース1–2 ではダブル UI を出さない。 */
    get needsDouble() {
      return this.isDoubleRace && this.heldCount === HELD_MAX && !this.myDoubleId;
    }

    get selectedTicket() {
      if (!this.selectedTicketId) return null;
      return this.stock.find((t) => t.ticketId === this.selectedTicketId) || null;
    }

    isSoldOut(ticket) {
      return !ticket || ticket.remaining === 0;
    }

    get canConfirm() {
      const ticket = this.selectedTicket;
      return Boolean(
        this.isMyTurn &&
          !this.pending &&
          ticket &&
          !this.isSoldOut(ticket) &&
          FACES.includes(this.selectedFace) &&
          this.heldCount < HELD_MAX
      );
    }

    get canSendDouble() {
      return Boolean(this.needsDouble && !this.pending);
    }

    get currentPlayerName() {
      const player = this.players.find((p) => p.playerId === this.currentPlayerId);
      return player ? player.displayName : "";
    }

    /* 山は Safe 面が上。選択時はセーフから始め、タップで裏返す（REQ-betting-002）。 */
    selectTicket(ticketId) {
      if (!this.isMyTurn || this.pending) return false;
      const ticket = this.stock.find((t) => t.ticketId === ticketId);
      if (this.isSoldOut(ticket) || this.heldCount >= HELD_MAX) return false;
      if (this.selectedTicketId !== ticketId) {
        this.selectedTicketId = ticketId;
        this.selectedFace = "safe";
      }
      this.error = "";
      return true;
    }

    toggleFace() {
      if (!this.isMyTurn || this.pending || !this.selectedTicket) return false;
      this.selectedFace = this.selectedFace === "risky" ? "safe" : "risky";
      return true;
    }

    chooseDouble(ticketInstanceId) {
      if (!this.canSendDouble) return false;
      return this.myPicks.some((p) => p.ticketInstanceId === ticketInstanceId);
    }

    buildPickRequest() {
      if (!this.canConfirm) return null;
      const ticket = this.selectedTicket;
      return { ticketKind: ticket.ticketKind, ticketId: ticket.ticketId, face: this.selectedFace };
    }

    buildDoubleRequest(ticketInstanceId) {
      if (!this.chooseDouble(ticketInstanceId)) return null;
      return { ticketInstanceId };
    }

    markPending() {
      this.pending = true;
      this.error = "";
    }

    /* 受信ペイロードは検証してからまとめて反映する。壊れていれば状態を進めない。 */
    applyState(payload) {
      if (!isObject(payload)) {
        this.error = MESSAGES.invalidState;
        return false;
      }
      let next;
      try {
        if (payload.phase !== "betting") throw new TypeError("phase");
        const raceIndex = payload.raceIndex;
        const round = payload.round;
        if (!Number.isInteger(raceIndex) || raceIndex < 1 || raceIndex > 3) throw new TypeError("raceIndex");
        if (!Number.isInteger(round) || round < 1) throw new TypeError("round");
        if (!Array.isArray(payload.stock) || !Array.isArray(payload.players)) throw new TypeError("list");
        if (!isObject(payload.picksByPlayer) || !isObject(payload.doubleByPlayer)) throw new TypeError("map");
        const currentPlayerId = payload.currentPlayerId;
        if (currentPlayerId !== null && !isText(currentPlayerId)) throw new TypeError("currentPlayerId");

        const stock = payload.stock.map(parseTicket);
        if (new Set(stock.map((t) => t.ticketId)).size !== stock.length) throw new TypeError("duplicate ticket");
        const players = payload.players.map(parsePlayer);
        const rawPicks = payload.picksByPlayer[this.myPlayerId];
        const myPicks = Array.isArray(rawPicks) ? rawPicks.map(parsePick) : [];
        if (myPicks.length > HELD_MAX) throw new TypeError("pick count");
        const rawDouble = payload.doubleByPlayer[this.myPlayerId];
        if (rawDouble !== undefined && rawDouble !== null && !isText(rawDouble)) throw new TypeError("double");
        const myDoubleId = isText(rawDouble) ? rawDouble : null;
        if (myDoubleId && !myPicks.some((p) => p.ticketInstanceId === myDoubleId)) throw new TypeError("double target");
        if (myDoubleId && raceIndex !== DOUBLE_RACE) throw new TypeError("double race");

        next = {
          raceIndex,
          round,
          turnIndex: isCount(payload.turnIndex) ? payload.turnIndex : 0,
          turnTotal: isCount(payload.turnTotal) ? payload.turnTotal : players.length,
          currentPlayerId: currentPlayerId === undefined ? null : currentPlayerId,
          stock,
          players,
          myPicks,
          myDoubleId,
        };
      } catch (error) {
        this.error = MESSAGES.invalidState;
        return false;
      }

      Object.assign(this, next);
      this.connected = true;
      this.pending = false;
      this.error = "";
      const selected = this.selectedTicket;
      if (!selected || this.isSoldOut(selected) || this.heldCount >= HELD_MAX || !this.isMyTurn) {
        this.selectedTicketId = null;
        this.selectedFace = null;
      }
      return true;
    }

    handleMessage(kind, payload) {
      if (this.advanced) return false;
      if (kind === "betting.state") return this.applyState(payload);
      if (kind === "betting.advanced") {
        if (!isObject(payload) || payload.phase !== "card-seed") return false;
        this.advanced = true;
        this.pending = false;
        this.error = "";
        this.selectedTicketId = null;
        this.selectedFace = null;
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

  return { BettingScreenState, MESSAGES, HELD_MAX, DOUBLE_RACE, FACES, TIERS, TICKET_KINDS };
});
