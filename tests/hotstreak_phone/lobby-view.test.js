/* CMP-lobby-011 / CMP-lobby-012 の描画を DOM スタブで検証する。 */
const test = require("node:test");
const assert = require("node:assert/strict");

const fakeDom = require("./fake-dom.js");
const { LobbyScreenState } = require("../../src/hotstreak_phone/lobby-state.js");

const ME = "p_1";

function player(playerId, displayName, nameReady) {
  return { playerId, displayName, nameReady, balance: nameReady ? 10 : 0 };
}

function payload(players) {
  return {
    sessionId: "sess_1",
    phase: "lobby",
    players: players || [player(ME, "", false), player("p_2", "サトウ", true), player("p_3", "", false)],
  };
}

function setup() {
  const nodes = fakeDom.install();
  delete require.cache[require.resolve("../../src/hotstreak_phone/lobby-view.js")];
  const { LobbyView } = require("../../src/hotstreak_phone/lobby-view.js");
  const calls = [];
  const view = new LobbyView({
    onNameInput: (text) => calls.push(["input", text]),
    onConfirm: () => calls.push(["confirm"]),
  });
  return { view, nodes, calls };
}

function stateOf(players) {
  const state = new LobbyScreenState();
  state.handleMessage("joined", Object.assign({ playerId: ME }, payload(players)));
  return state;
}

test("参加者の人数と一覧を表示し、自分の行を示す", () => {
  const { view, nodes } = setup();
  view.render(stateOf());
  assert.equal(nodes["player-count"].textContent, "参加者 3 人");
  const rows = nodes["player-list"].children;
  assert.equal(rows.length, 3);
  assert.equal(rows[0].dataset.self, "true");
  assert.match(rows[0].text, /（自分）/);
  assert.equal(rows[1].dataset.self, "false");
  assert.match(rows[1].text, /サトウ/);
});

test("未入力の人は名前を伏せて入力中と出す", () => {
  const { view, nodes } = setup();
  view.render(stateOf());
  const [me, sato] = nodes["player-list"].children;
  assert.match(me.text, /（入力中）/);
  assert.match(me.findByClass("player-status").textContent, /入力中/);
  assert.match(sato.findByClass("player-status").textContent, /入力済/);
});

test("入力すると通知し、非空で確定できるようになる", () => {
  const { view, nodes, calls } = setup();
  const state = stateOf();
  view.render(state);
  assert.equal(nodes["confirm-button"].disabled, true);

  nodes["name-input"].type("ヤマダ");
  assert.deepEqual(calls, [["input", "ヤマダ"]]);

  state.setDraftName("ヤマダ");
  view.render(state);
  assert.equal(nodes["confirm-button"].disabled, false);
  nodes["confirm-button"].click();
  assert.deepEqual(calls, [["input", "ヤマダ"], ["confirm"]]);
});

test("確定後は入力欄を閉じ、待ちを案内する", () => {
  const { view, nodes } = setup();
  const state = stateOf();
  state.applyState(payload([player(ME, "ヤマダ", true), player("p_2", "サトウ", true), player("p_3", "", false)]));
  view.render(state);
  assert.equal(nodes["name-input"].disabled, true);
  assert.equal(nodes["name-input"].value, "ヤマダ");
  assert.equal(nodes["confirm-button"].disabled, true);
  assert.match(nodes.notice.textContent, /ほかの人の入力を待って/);
});

test("全員そろったら待機案内にする", () => {
  const { view, nodes } = setup();
  const state = stateOf([
    player(ME, "ヤマダ", true),
    player("p_2", "サトウ", true),
    player("p_3", "タナカ", true),
  ]);
  view.render(state);
  assert.match(nodes.notice.textContent, /全員そろいました/);
});

test("送信中はボタンを止める", () => {
  const { view, nodes } = setup();
  const state = stateOf();
  state.setDraftName("ヤマダ");
  state.markPending();
  view.render(state);
  assert.equal(nodes["confirm-button"].disabled, true);
  assert.equal(nodes["confirm-button"].textContent, "送信中…");
});

test("進行後は確定ボタンを隠し、公開カードの準備中と案内する", () => {
  const { view, nodes } = setup();
  const state = stateOf();
  state.handleMessage("lobby.advanced", { phase: "setup-cards" });
  view.render(state);
  assert.equal(nodes["confirm-button"].hidden, true);
  assert.equal(nodes["foot-hint"].hidden, true);
  assert.equal(nodes["name-input"].disabled, true);
  assert.match(nodes.notice.textContent, /公開カードの準備中/);
});

test("エラーは赤字で出す", () => {
  const { view, nodes } = setup();
  const state = stateOf();
  state.handleMessage("error", { message: "参加人数が上限です" });
  view.render(state);
  assert.equal(nodes.notice.textContent, "参加人数が上限です");
  assert.equal(nodes.notice.dataset.error, "true");
});
