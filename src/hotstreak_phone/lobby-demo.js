/* サーバ無しで画面を確認するための偽データ。ゲームルールの検証には使えない。 */
(function (root, factory) {
  const api = factory();
  if (typeof module === "object" && module.exports) module.exports = api;
  else root.HotStreakLobbyDemo = api;
})(typeof globalThis !== "undefined" ? globalThis : this, function () {
  const ME = "p_1";

  function player(playerId, displayName, nameReady) {
    return { playerId, displayName, nameReady, balance: nameReady ? 10 : 0 };
  }

  function state(players) {
    return { sessionId: "sess_demo", phase: "lobby", players };
  }

  const SCENES = [
    {
      name: "参加直後（4人・自分は未入力）",
      make: () =>
        state([
          player(ME, "", false),
          player("p_2", "サトウ", true),
          player("p_3", "", false),
          player("p_4", "", false),
        ]),
    },
    {
      name: "ほかの人が入力を進める",
      make: (current) =>
        state([
          current.players[0],
          player("p_2", "サトウ", true),
          player("p_3", "タナカ", true),
          player("p_4", "", false),
        ]),
    },
    {
      name: "全員そろった",
      make: (current) =>
        state([
          current.players[0].nameReady ? current.players[0] : player(ME, "ヤマダ", true),
          player("p_2", "サトウ", true),
          player("p_3", "タナカ", true),
          player("p_4", "プレイヤー4", true),
        ]),
    },
    { name: "公開カードの準備中", make: () => "lobby-advanced" },
    { name: "マ券ドラフトへ", make: () => "setup-advanced" },
  ];

  class DemoDriver {
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
      this.onMessage("joined", Object.assign({ playerId: ME }, this.current));
    }

    close() {}

    next() {
      this.index = (this.index + 1) % SCENES.length;
      this.show();
      return this.sceneName;
    }

    show() {
      const scene = SCENES[this.index].make(this.current);
      if (scene === "lobby-advanced") {
        this.onMessage("lobby.advanced", { phase: "setup-cards" });
        return;
      }
      if (scene === "setup-advanced") {
        this.onMessage("setup.advanced", { phase: "betting" });
        return;
      }
      this.current = scene;
      this.onMessage("lobby.state", scene);
    }

    sendName(body) {
      const players = this.current.players.map((entry) =>
        entry.playerId === ME ? player(ME, body.displayName, true) : entry
      );
      this.current = state(players);
      this.onMessage("lobby.state", this.current);
      return Promise.resolve(true);
    }
  }

  return { DemoDriver, DEMO_PLAYER_ID: ME };
});
