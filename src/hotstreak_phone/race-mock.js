/* 固定データのモック。通信はしない（Display 側 RACE_MOCK.md と同じ方針）。
   マスコット名は data/cards/catalog.json の mascot_name_mapping に合わせている。 */
(function (root, factory) {
  const api = factory();
  if (typeof module === "object" && module.exports) module.exports = api;
  else root.HotStreakRaceMock = api;
})(typeof globalThis !== "undefined" ? globalThis : this, function () {
  const ME = "p_1";

  const MASCOTS = [
    { mascotId: "blue", displayName: "ダングル", color: "blue" },
    { mascotId: "orange", displayName: "ゴブラー", color: "orange" },
    { mascotId: "yellow", displayName: "マム", color: "yellow" },
    { mascotId: "salmon", displayName: "ハーレー", color: "salmon" },
  ];

  function mascots(order, marks) {
    return order.map((mascotId, index) => {
      const base = MASCOTS.find((m) => m.mascotId === mascotId);
      return Object.assign({}, base, {
        rank: index + 1,
        finished: (marks.finished || []).includes(mascotId),
        disqualified: (marks.disqualified || []).includes(mascotId),
      });
    });
  }

  function bet(ticketInstanceId, label, face, double) {
    return { ticketInstanceId, label, face, double: Boolean(double) };
  }

  function players(balances) {
    return [
      { playerId: ME, displayName: "ヤマダ", balance: balances[0], rank: 2,
        bets: [bet("t-1", "ダングル", "risky"), bet("t-2", "サイド YES", "safe")] },
      { playerId: "p_2", displayName: "サトウ", balance: balances[1], rank: 1,
        bets: [bet("t-3", "ゴブラー", "safe"), bet("t-4", "マム", "safe")] },
      { playerId: "p_3", displayName: "タナカ", balance: balances[2], rank: 3,
        bets: [bet("t-5", "ハーレー", "risky"), bet("t-6", "サイド NO", "risky")] },
      { playerId: "p_4", displayName: "スズキ", balance: balances[3], rank: 4,
        bets: [bet("t-7", "マム", "risky"), bet("t-8", "ダングル", "safe")] },
    ];
  }

  function state(overrides) {
    return Object.assign(
      {
        phase: "race",
        raceIndex: 2,
        prompt: { text: "コースアウトするマスコットはいる？" },
        mascots: mascots(["blue", "orange", "yellow", "salmon"], {}),
        players: players([14, 18, 11, 9]),
      },
      overrides
    );
  }

  const SCENES = [
    { name: "レース序盤", make: () => state() },
    {
      name: "順位が入れ替わる",
      make: () => state({ mascots: mascots(["yellow", "blue", "salmon", "orange"], {}) }),
    },
    {
      name: "ゴールと失格が出る",
      make: () =>
        state({
          mascots: mascots(["yellow", "blue", "salmon", "orange"], {
            finished: ["yellow", "blue"],
            disqualified: ["orange"],
          }),
        }),
    },
    { name: "レース終了（配当へ）", make: () => ({ finished: true }) },
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
      this.onMessage("race.state", SCENES[0].make());
    }

    close() {}

    next() {
      this.index = (this.index + 1) % SCENES.length;
      const scene = SCENES[this.index].make();
      if (scene.finished) this.onMessage("race.finished", { phase: "payout" });
      else this.onMessage("race.state", scene);
      return this.sceneName;
    }
  }

  return { MockDriver, MOCK_PLAYER_ID: ME, MASCOTS };
});
