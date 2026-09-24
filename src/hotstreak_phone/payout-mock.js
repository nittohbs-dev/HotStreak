/* 固定データのモック。通信・精算はしない（Display 側 PAYOUT_MOCK.md と同じ方針）。
   マスコット名は data/cards/catalog.json の mascot_name_mapping、金額は payout README の観測確定額表に合わせている。 */
(function (root, factory) {
  const api = factory();
  if (typeof module === "object" && module.exports) module.exports = api;
  else root.HotStreakPayoutMock = api;
})(typeof globalThis !== "undefined" ? globalThis : this, function () {
  const ME = "p_1";

  const MASCOTS = [
    { mascotId: "blue", displayName: "ダングル", color: "blue" },
    { mascotId: "orange", displayName: "ゴブラー", color: "orange" },
    { mascotId: "yellow", displayName: "マム", color: "yellow" },
    { mascotId: "salmon", displayName: "ハーレー", color: "salmon" },
  ];

  const NAMES = { p_1: "ヤマダ", p_2: "サトウ", p_3: "タナカ", p_4: "スズキ" };

  function standings(order, disqualified) {
    return order.map((mascotId, index) => {
      const base = MASCOTS.find((m) => m.mascotId === mascotId);
      return Object.assign({}, base, { rank: index + 1, disqualified: (disqualified || []).includes(mascotId) });
    });
  }

  /* rows: [playerId, balance, delta, rank] */
  function balances(rows) {
    return rows.map(([playerId, balance, delta, rank]) => ({
      playerId, displayName: NAMES[playerId], balance, delta, rank,
    }));
  }

  function item(ticketInstanceId, label, kind, face, tier, amount, double) {
    return { ticketInstanceId, label, kind, face, tier, amount, double: Boolean(double) };
  }

  function breakdown(items) {
    return { playerId: ME, total: items.reduce((sum, row) => sum + row.amount, 0), items };
  }

  const SCENES = [
    {
      name: "レース1結果",
      /* リスキー mid 2着 $3、サイド リスキー外れ -$5。 */
      make: () => ({
        phase: "payout",
        raceIndex: 1,
        standings: standings(["yellow", "blue", "salmon", "orange"]),
        myBreakdown: breakdown([
          item("t-1", "ダングル", "mascot", "risky", "mid", 3),
          item("t-2", "サイド YES", "side", "risky", "top", -5),
        ]),
        balances: balances([["p_3", 24, 14, 1], ["p_4", 21, 11, 2], ["p_2", 17, 7, 3], [ME, 8, -2, 4]]),
      }),
    },
    {
      name: "レース3結果",
      /* 第3のダブル札が外れて -$5×2。スズキは下限 $0。 */
      make: () => ({
        phase: "payout",
        raceIndex: 3,
        standings: standings(["blue", "salmon", "yellow", "orange"], ["orange"]),
        myBreakdown: breakdown([
          item("t-11", "ダングル", "mascot", "safe", "top", 10),
          item("t-12", "サイド NO", "side", "risky", "bot", -10, true),
        ]),
        balances: balances([["p_2", 25, 8, 1], [ME, 20, 0, 2], ["p_3", 19, -3, 3], ["p_4", 0, -4, 4]]),
        winners: ["p_2"],
      }),
    },
    {
      name: "レース3・共同優勝",
      /* ダブル札が1着 $10×2。サトウと同額で共同優勝。 */
      make: () => ({
        phase: "payout",
        raceIndex: 3,
        standings: standings(["blue", "salmon", "yellow", "orange"], ["orange"]),
        myBreakdown: breakdown([
          item("t-11", "ダングル", "mascot", "safe", "top", 20, true),
          item("t-12", "サイド NO", "side", "risky", "bot", -5),
        ]),
        balances: balances([["p_2", 25, 8, 1], [ME, 25, 15, 1], ["p_3", 19, -3, 3], ["p_4", 0, -4, 4]]),
        winners: ["p_2", ME],
      }),
    },
    { name: "Enter 後（ロビーへ）", make: () => ({ advanced: "lobby" }) },
  ];

  class MockDriver {
    constructor(onMessage) {
      this.onMessage = onMessage;
      this.index = 0;
      this.playerId = ME;
    }

    get sceneName() {
      return SCENES[this.index].name;
    }

    start() {
      this.onMessage("payout.state", SCENES[0].make());
    }

    close() {}

    next() {
      this.index = (this.index + 1) % SCENES.length;
      const scene = SCENES[this.index].make();
      if (scene.advanced) this.onMessage("payout.advanced", { phase: scene.advanced });
      else this.onMessage("payout.state", scene);
      return this.sceneName;
    }
  }

  return { MockDriver, MOCK_PLAYER_ID: ME, MASCOTS };
});
