/* サーバ無しで画面を確認するための偽データ。ゲームルールの検証には使えない。 */
(function (root, factory) {
  const api = factory();
  if (typeof module === "object" && module.exports) module.exports = api;
  else root.HotStreakBettingDemo = api;
})(typeof globalThis !== "undefined" ? globalThis : this, function () {
  const ME = "p1";
  const PLAYERS = [
    { playerId: ME, displayName: "ヤマダ" },
    { playerId: "p2", displayName: "サトウ" },
    { playerId: "p3", displayName: "プレイヤー3" },
    { playerId: "p4", displayName: "プレイヤー4" },
  ];

  function stock(soldOut) {
    const rows = [
      { ticketId: "mascot-bear", ticketKind: "mascot", label: "くま", tier: "top", remaining: 3 },
      { ticketId: "mascot-fish", ticketKind: "mascot", label: "さかな", tier: "mid", remaining: 2 },
      { ticketId: "mascot-bird", ticketKind: "mascot", label: "とり", tier: "bot", remaining: 3 },
      { ticketId: "mascot-rabbit", ticketKind: "mascot", label: "うさぎ", tier: "top", remaining: 1 },
      { ticketId: "side-yes", ticketKind: "side", label: "サイド YES", tier: "top", remaining: 3 },
      { ticketId: "side-no", ticketKind: "side", label: "サイド NO", tier: "mid", remaining: 3 },
    ];
    return rows.map((row) => (soldOut.includes(row.ticketId) ? Object.assign({}, row, { remaining: 0 }) : row));
  }

  function base(overrides) {
    return Object.assign(
      {
        phase: "betting",
        raceIndex: 1,
        round: 1,
        turnIndex: 1,
        turnTotal: 4,
        currentPlayerId: ME,
        prompt: { promptId: "sb-03", text: "コースアウトするマスコットはいる？" },
        stock: stock([]),
        players: PLAYERS,
        picksByPlayer: {},
        doubleByPlayer: {},
      },
      overrides
    );
  }

  const BEAR_PICK = {
    ticketInstanceId: "t-1",
    ticketId: "mascot-bear",
    ticketKind: "mascot",
    label: "くま",
    tier: "top",
    face: "risky",
  };
  const YES_PICK = {
    ticketInstanceId: "t-2",
    ticketId: "side-yes",
    ticketKind: "side",
    label: "サイド YES",
    tier: "top",
    face: "safe",
  };

  const SCENES = [
    { name: "他の人の番", make: () => base({ currentPlayerId: "p2", turnIndex: 2 }) },
    { name: "自分の番・所持0", make: () => base({}) },
    {
      name: "自分の番・所持1枚・在庫0あり",
      make: () =>
        base({
          round: 2,
          turnIndex: 3,
          stock: stock(["mascot-rabbit", "side-no"]),
          picksByPlayer: { [ME]: [BEAR_PICK] },
        }),
    },
    {
      name: "第3レース・ダブル指定",
      make: () =>
        base({
          raceIndex: 3,
          round: 2,
          turnIndex: 4,
          currentPlayerId: "p4",
          picksByPlayer: { [ME]: [BEAR_PICK, YES_PICK] },
        }),
    },
    { name: "切断", make: () => null },
    { name: "仕込みへ進行", make: () => "advanced" },
  ];

  class DemoDriver {
    constructor(onMessage) {
      this.onMessage = onMessage;
      this.index = 0;
      this.current = null;
    }

    get sceneName() {
      return SCENES[this.index].name;
    }

    start() {
      this.show();
    }

    close() {}

    next() {
      this.index = (this.index + 1) % SCENES.length;
      this.show();
      return this.sceneName;
    }

    show() {
      const scene = SCENES[this.index].make();
      if (scene === null) {
        this.onMessage("disconnected", {});
        return;
      }
      if (scene === "advanced") {
        this.onMessage("betting.advanced", { phase: "card-seed" });
        return;
      }
      this.current = scene;
      this.onMessage("betting.state", scene);
    }

    sendPick(body) {
      if (!this.current) return Promise.resolve(false);
      const next = JSON.parse(JSON.stringify(this.current));
      const ticket = next.stock.find((t) => t.ticketId === body.ticketId);
      ticket.remaining -= 1;
      const picks = next.picksByPlayer[ME] || [];
      picks.push({
        ticketInstanceId: `demo-${picks.length + 1}`,
        ticketId: ticket.ticketId,
        ticketKind: ticket.ticketKind,
        label: ticket.label,
        tier: ticket.tier,
        face: body.face,
      });
      next.picksByPlayer[ME] = picks;
      next.currentPlayerId = "p2";
      next.turnIndex = Math.min(next.turnTotal, next.turnIndex + 1);
      this.current = next;
      this.onMessage("betting.state", next);
      return Promise.resolve(true);
    }

    sendDouble(body) {
      if (!this.current) return Promise.resolve(false);
      const next = JSON.parse(JSON.stringify(this.current));
      next.doubleByPlayer[ME] = body.ticketInstanceId;
      this.current = next;
      this.onMessage("betting.state", next);
      return Promise.resolve(true);
    }
  }

  return { DemoDriver, DEMO_PLAYER_ID: ME };
});
