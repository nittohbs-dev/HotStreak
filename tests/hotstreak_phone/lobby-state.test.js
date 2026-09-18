/* SCR-phone-001 状態ロジックの検証。node --test で実行する（追加依存なし）。 */
const test = require("node:test");
const assert = require("node:assert/strict");

const { LobbyScreenState } = require("../../src/hotstreak_phone/lobby-state.js");

const ME = "p_1";

function player(playerId, displayName, nameReady) {
  return { playerId, displayName, nameReady, balance: nameReady ? 10 : 0 };
}

function payload(overrides) {
  return Object.assign(
    {
      sessionId: "sess_1",
      phase: "lobby",
      players: [player(ME, "", false), player("p_2", "サトウ", true), player("p_3", "", false)],
    },
    overrides
  );
}

function joined(overrides) {
  const state = new LobbyScreenState();
  assert.equal(state.handleMessage("joined", Object.assign({ playerId: ME }, payload(overrides))), true);
  return state;
}

test("join の応答で playerId と参加者一覧を受け取る", () => {
  const state = joined();
  assert.equal(state.playerId, ME);
  assert.equal(state.connected, true);
  assert.equal(state.playerCount, 3);
  assert.equal(state.me.playerId, ME);
  assert.equal(state.isNameReady, false);
});

test("playerId が無い join 応答は受け付けない", () => {
  const state = new LobbyScreenState();
  assert.equal(state.handleMessage("joined", payload()), false);
  assert.equal(state.playerId, null);
  assert.notEqual(state.error, "");
});

test("空名・空白のみでは確定できず API も呼ばない", () => {
  const state = joined();
  assert.equal(state.canSubmit, false);
  state.setDraftName("   ");
  assert.equal(state.canSubmit, false);
  assert.equal(state.buildNameRequest(), null);

  state.setDraftName(" ヤマダ ");
  assert.equal(state.canSubmit, true);
  assert.deepEqual(state.buildNameRequest(), { displayName: "ヤマダ" });
});

test("送信中は二重に確定できない", () => {
  const state = joined();
  state.setDraftName("ヤマダ");
  state.markPending();
  assert.equal(state.canSubmit, false);
  assert.equal(state.buildNameRequest(), null);
});

test("確定後は入力も再送もできない", () => {
  const state = joined();
  state.setDraftName("ヤマダ");
  state.applyState(payload({ players: [player(ME, "ヤマダ", true), player("p_2", "サトウ", true)] }));
  assert.equal(state.isNameReady, true);
  assert.equal(state.canSubmit, false);
  assert.equal(state.setDraftName("タナカ"), false);
  assert.equal(state.draftName, "ヤマダ", "サーバの確定名を表示する");
});

test("全員そろうのは3人以上で全員入力済のとき", () => {
  const two = joined({ players: [player(ME, "ヤマダ", true), player("p_2", "サトウ", true)] });
  assert.equal(two.allReady, false, "3人未満は進行できない");

  const three = joined({
    players: [player(ME, "ヤマダ", true), player("p_2", "サトウ", true), player("p_3", "タナカ", true)],
  });
  assert.equal(three.allReady, true);

  const pending = joined();
  assert.equal(pending.allReady, false);
});

test("lobby.advanced は一度だけ受け付ける", () => {
  const state = joined();
  assert.equal(state.handleMessage("lobby.advanced", { phase: "setup-cards" }), true);
  assert.equal(state.advanced, true);
  assert.equal(state.canSubmit, false);
  assert.equal(state.handleMessage("lobby.advanced", { phase: "setup-cards" }), false);
  assert.equal(state.handleMessage("lobby.advanced", { phase: "betting" }), false);
});

test("setup.advanced でマ券画面への引き渡しに入る", () => {
  const state = joined();
  state.handleMessage("lobby.advanced", { phase: "setup-cards" });
  assert.equal(state.handleMessage("setup.advanced", { phase: "betting" }), true);
  assert.equal(state.handoff, true);
  assert.equal(state.handleMessage("lobby.state", payload()), false, "引き渡し後は状態を動かさない");
});

test("壊れた payload では状態を進めない", () => {
  const state = joined();
  const broken = [
    payload({ phase: "setup-cards" }),
    payload({ players: null }),
    payload({ players: [{ playerId: ME }] }),
    payload({ players: [player(ME, "", true)] }),
    payload({ players: [player(ME, "ヤマダ", true), player(ME, "サトウ", true)] }),
    payload({ players: new Array(9).fill(null).map((_, index) => player(`p_${index}`, "", false)) }),
    "not-json",
  ];
  for (const bad of broken) {
    assert.equal(state.applyState(bad), false);
    assert.equal(state.playerCount, 3, "直前の状態を保つ");
    assert.notEqual(state.error, "");
  }
});

test("切断で送信を止め、サーバのエラー文言を表示する", () => {
  const state = joined();
  state.setDraftName("ヤマダ");
  state.markPending();
  state.handleMessage("disconnected", {});
  assert.equal(state.connected, false);
  assert.equal(state.pending, false);
  assert.equal(state.canSubmit, false);

  state.applyState(payload());
  state.markPending();
  state.handleMessage("error", { message: "参加人数が上限です" });
  assert.equal(state.pending, false);
  assert.equal(state.error, "参加人数が上限です");
});
