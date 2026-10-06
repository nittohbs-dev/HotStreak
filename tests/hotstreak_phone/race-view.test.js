/* CMP-race-011〜014 の描画を DOM スタブで検証する。 */
const test = require("node:test");
const assert = require("node:assert/strict");

const fakeDom = require("./fake-dom.js");
const { RaceScreenState } = require("../../src/hotstreak_phone/race-state.js");

const ME = "p_1";

function mascot(mascotId, displayName, rank, extra) {
  return Object.assign({ mascotId, displayName, color: mascotId, rank }, extra || {});
}

function bet(ticketInstanceId, label, face, double) {
  return { ticketInstanceId, label, face, double: Boolean(double) };
}

function payload(overrides) {
  return Object.assign(
    {
      phase: "race",
      raceIndex: 2,
      prompt: { text: "コースアウトするマスコットはいる？" },
      mascots: [
        mascot("yellow", "マム", 1),
        mascot("blue", "ダングル", 2),
        mascot("salmon", "ハーレー", 3),
        mascot("orange", "ゴブラー", 4),
      ],
      players: [
        { playerId: ME, displayName: "ヤマダ", rank: 2, balance: 14,
          bets: [bet("t-1", "ダングル", "risky"), bet("t-2", "サイド YES", "safe", true)] },
        { playerId: "p_2", displayName: "サトウ", rank: 1, balance: 18, bets: [bet("t-3", "ゴブラー", "safe")] },
      ],
      myBets: [bet("t-1", "ダングル", "risky"), bet("t-2", "サイド YES", "safe", true)],
    },
    overrides
  );
}

function setup() {
  const nodes = fakeDom.install();
  delete require.cache[require.resolve("../../src/hotstreak_phone/race-view.js")];
  const { RaceView } = require("../../src/hotstreak_phone/race-view.js");
  const calls = [];
  const view = new RaceView({
    onOpenSheet: () => calls.push(["open"]),
    onCloseSheet: () => calls.push(["close"]),
  });
  return { view, nodes, calls };
}

function stateOf(overrides) {
  const state = new RaceScreenState(ME);
  assert.equal(state.applyState(payload(overrides)), true);
  return state;
}

test("お題を出す", () => {
  const { view, nodes } = setup();
  view.render(stateOf());
  assert.equal(nodes["side-prompt"].textContent, "コースアウトするマスコットはいる？");
});

test("お題が未取得なら確認中を出す", () => {
  const { view, nodes } = setup();
  view.render(stateOf({ prompt: null }));
  assert.match(nodes["side-prompt"].textContent, /確認しています/);
});

test("そのレースで購入した自分のマ券を出す", () => {
  const { view, nodes } = setup();
  view.render(stateOf());
  const chips = nodes["my-bets"].children;
  assert.equal(chips.length, 2);
  assert.match(chips[0].text, /ダングル/);
  assert.match(chips[0].text, /リスキー/);
  assert.match(chips[1].text, /★ダブル/);
});

test("接続後に購入マ券が無ければ余計な表示を出さない", () => {
  const { view, nodes } = setup();
  view.render(
    stateOf({
      myBets: [],
    })
  );
  assert.equal(nodes["my-bets"].children.length, 0);
});
