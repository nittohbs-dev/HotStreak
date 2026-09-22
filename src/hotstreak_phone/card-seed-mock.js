/* 固定データのモック。通信はしない（Display 側 CARD_SEED_MOCK.md と同じ方針）。
   カード定義は data/cards/catalog.json からの転記。file:// では読み込めないため手札分だけ写している。 */
(function (root, factory) {
  const api = factory();
  if (typeof module === "object" && module.exports) module.exports = api;
  else root.HotStreakCardSeedMock = api;
})(typeof globalThis !== "undefined" ? globalThis : this, function () {
  const ME = "p_1";

  const CARDS = [
    { cardId: "blue_move_3", color: "blue", label: "移動", rect: [1200, 0, 240, 336] },
    { cardId: "orange_turn", color: "orange", label: "方向転換", rect: [720, 672, 240, 336] },
    { cardId: "yellow_star", color: "yellow", label: "スター", rect: [720, 1680, 240, 336] },
  ];

  function progress(seededIds) {
    return [
      { playerId: ME, displayName: "ヤマダ", seeded: seededIds.includes(ME) },
      { playerId: "p_2", displayName: "サトウ", seeded: seededIds.includes("p_2") },
      { playerId: "p_3", displayName: "タナカ", seeded: seededIds.includes("p_3") },
      { playerId: "p_4", displayName: "スズキ", seeded: seededIds.includes("p_4") },
    ];
  }

  function state(overrides) {
    return Object.assign(
      {
        phase: "card-seed",
        raceIndex: 2,
        deckCountExpected: 18,
        hand: CARDS.slice(),
        progress: progress(["p_2"]),
        seededCard: null,
      },
      overrides
    );
  }

  function mySeeded(current) {
    return current.progress.find((entry) => entry.playerId === ME).seeded;
  }

  const SCENES = [
    { name: "手札3枚・自分は未仕込み", make: () => state() },
    {
      name: "自分以外は全員仕込み済み",
      make: (current) =>
        Object.assign(state(), {
          hand: current.hand,
          seededCard: current.seededCard,
          progress: progress(["p_2", "p_3", "p_4"].concat(mySeeded(current) ? [ME] : [])),
        }),
    },
    {
      // 自分が未仕込みなら、先頭の手札を仕込んだ扱いにする。
      name: "全員仕込み済み",
      make: (current) =>
        Object.assign(state(), {
          hand: mySeeded(current) ? current.hand : current.hand.slice(1),
          seededCard: mySeeded(current) ? current.seededCard : current.hand[0],
          progress: progress([ME, "p_2", "p_3", "p_4"]),
        }),
    },
    { name: "レースへ進行", make: () => ({ advanced: true }) },
  ];

  class MockDriver {
    constructor(onMessage) {
      this.onMessage = onMessage;
      this.index = 0;
      this.current = null;
      this.playerId = ME;
    }

    get sceneName() {
      return SCENES[this.index].name;
    }

    start() {
      this.current = SCENES[0].make();
      this.onMessage("seed.state", this.current);
    }

    close() {}

    next() {
      this.index = (this.index + 1) % SCENES.length;
      this.show();
      return this.sceneName;
    }

    show() {
      const scene = SCENES[this.index].make(this.current);
      if (scene.advanced) {
        this.onMessage("seed.advanced", { phase: "race" });
        return;
      }
      this.current = scene;
      this.onMessage("seed.state", scene);
    }

    /* 仕込むと手札から1枚抜け、自分が「済」になる（確定後の取り消しは無い）。 */
    sendSeed(body) {
      const next = JSON.parse(JSON.stringify(this.current));
      next.seededCard = next.hand.find((card) => card.cardId === body.handCardId) || null;
      next.hand = next.hand.filter((card) => card.cardId !== body.handCardId);
      next.progress = next.progress.map((entry) =>
        entry.playerId === ME ? Object.assign({}, entry, { seeded: true }) : entry
      );
      this.current = next;
      this.onMessage("seed.state", next);
      return Promise.resolve(true);
    }
  }

  return { MockDriver, MOCK_PLAYER_ID: ME, CARDS };
});
