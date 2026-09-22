/* CLS-seed-011 の状態部。DOM・通信を持たない。SCR-phone-003 / REQ-seed-001, 003, 004。 */
(function (root, factory) {
  const api = factory();
  if (typeof module === "object" && module.exports) module.exports = api;
  else root.HotStreakCardSeedState = api;
})(typeof globalThis !== "undefined" ? globalThis : this, function () {
  const HAND_MAX = 3;

  const MESSAGES = {
    invalidState: "仕込みの情報を確認できません。画面を開き直してください。",
  };

  function isObject(value) {
    return typeof value === "object" && value !== null && !Array.isArray(value);
  }

  function isText(value) {
    return typeof value === "string" && value.length > 0;
  }

  function parseRect(raw) {
    if (!Array.isArray(raw) || raw.length !== 4 || !raw.every((n) => Number.isInteger(n) && n >= 0)) {
      throw new TypeError("rect");
    }
    return raw.slice();
  }

  function parseCard(raw) {
    if (!isObject(raw) || !isText(raw.cardId) || !isText(raw.label)) throw new TypeError("card");
    return {
      cardId: raw.cardId,
      label: raw.label,
      color: isText(raw.color) ? raw.color : "",
      rect: parseRect(raw.rect),
    };
  }

  function parseProgress(raw) {
    if (!isObject(raw) || !isText(raw.playerId) || typeof raw.seeded !== "boolean") throw new TypeError("progress");
    return {
      playerId: raw.playerId,
      displayName: isText(raw.displayName) ? raw.displayName : raw.playerId,
      seeded: raw.seeded,
    };
  }

  class CardSeedScreenState {
    constructor(myPlayerId) {
      this.myPlayerId = myPlayerId || "";
      this.connected = false;
      this.pending = false;
      this.advanced = false;
      this.error = "";
      this.raceIndex = 0;
      this.hand = [];
      this.progress = [];
      this.deckCountExpected = 0;
      this.selectedCardId = null;
      this.seededCard = null;
    }

    get me() {
      return this.progress.find((entry) => entry.playerId === this.myPlayerId) || null;
    }

    /* BR-seed-005: 確定後は変更できない。 */
    get seeded() {
      return Boolean(this.me && this.me.seeded);
    }

    get handCount() {
      return this.hand.length;
    }

    get seededCount() {
      return this.progress.filter((entry) => entry.seeded).length;
    }

    get playerTotal() {
      return this.progress.length;
    }

    get allSeeded() {
      return this.playerTotal > 0 && this.seededCount === this.playerTotal;
    }

    get selectedCard() {
      if (!this.selectedCardId) return null;
      return this.hand.find((card) => card.cardId === this.selectedCardId) || null;
    }

    canSelect(cardId) {
      return Boolean(
        this.connected && !this.seeded && !this.pending && !this.advanced && this.hand.some((c) => c.cardId === cardId)
      );
    }

    get canConfirm() {
      return Boolean(this.selectedCard && this.canSelect(this.selectedCardId));
    }

    selectCard(cardId) {
      if (!this.canSelect(cardId)) return false;
      this.selectedCardId = cardId;
      this.error = "";
      return true;
    }

    buildSeedRequest() {
      if (!this.canConfirm) return null;
      return { handCardId: this.selectedCardId };
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
        if (payload.phase !== "card-seed") throw new TypeError("phase");
        const raceIndex = payload.raceIndex;
        if (!Number.isInteger(raceIndex) || raceIndex < 1 || raceIndex > 3) throw new TypeError("raceIndex");
        if (!Array.isArray(payload.hand) || !Array.isArray(payload.progress)) throw new TypeError("list");
        const hand = payload.hand.map(parseCard);
        if (hand.length > HAND_MAX) throw new TypeError("hand count");
        if (new Set(hand.map((c) => c.cardId)).size !== hand.length) throw new TypeError("duplicate card");
        const progress = payload.progress.map(parseProgress);
        if (new Set(progress.map((p) => p.playerId)).size !== progress.length) throw new TypeError("duplicate player");
        const deckCountExpected = payload.deckCountExpected;
        if (!Number.isInteger(deckCountExpected) || deckCountExpected < 0) throw new TypeError("deckCount");
        // 自分が仕込んだ札は本人にだけ見せる（BR-seed-004 の非公開は他プレイヤーに対するもの）。
        const seededCard = payload.seededCard === undefined || payload.seededCard === null
          ? null
          : parseCard(payload.seededCard);
        next = { raceIndex, hand, progress, deckCountExpected, seededCard };
      } catch (error) {
        this.error = MESSAGES.invalidState;
        return false;
      }

      Object.assign(this, next);
      this.connected = true;
      this.pending = false;
      this.error = "";
      if (!this.selectedCard || this.seeded) this.selectedCardId = null;
      return true;
    }

    handleMessage(kind, payload) {
      if (this.advanced) return false;
      if (kind === "seed.state") return this.applyState(payload);
      if (kind === "seed.advanced") {
        if (!isObject(payload) || payload.phase !== "race") return false;
        this.advanced = true;
        this.pending = false;
        this.error = "";
        this.selectedCardId = null;
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

  return { CardSeedScreenState, MESSAGES, HAND_MAX };
});
