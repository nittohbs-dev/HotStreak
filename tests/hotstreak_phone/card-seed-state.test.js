/* SCR-phone-003 状態ロジックの検証。node --test で実行する（追加依存なし）。 */
const test = require("node:test");
const assert = require("node:assert/strict");

const { CardSeedScreenState } = require("../../src/hotstreak_phone/card-seed-state.js");

const ME = "p_1";

function card(cardId, label, rect) {
  return { cardId, label, color: "blue", rect: rect || [0, 0, 240, 336] };
}

function progress(seededIds) {
  return ["p_1", "p_2", "p_3", "p_4"].map((playerId) => ({
    playerId,
    displayName: playerId === ME ? "ヤマダ" : playerId,
    seeded: seededIds.includes(playerId),
  }));
}

function payload(overrides) {
  return Object.assign(
    {
      phase: "card-seed",
      raceIndex: 2,
      deckCountExpected: 18,
      hand: [card("blue_move_3", "移動"), card("orange_turn", "方向転換"), card("yellow_star", "スター")],
      progress: progress(["p_2"]),
    },
    overrides
  );
}

function ready(overrides) {
  const state = new CardSeedScreenState(ME);
  assert.equal(state.applyState(payload(overrides)), true);
  return state;
}

test("state を受けるとレース・手札・進捗が反映される", () => {
  const state = ready();
  assert.equal(state.raceIndex, 2);
  assert.equal(state.handCount, 3);
  assert.equal(state.seededCount, 1);
  assert.equal(state.playerTotal, 4);
  assert.equal(state.deckCountExpected, 18);
  assert.equal(state.seeded, false);
  assert.equal(state.allSeeded, false);
});

test("未選択では確定できない", () => {
  const state = ready();
  assert.equal(state.canConfirm, false);
  assert.equal(state.buildSeedRequest(), null);
});

test("手札から1枚選ぶと確定できる", () => {
  const state = ready();
  assert.equal(state.selectCard("orange_turn"), true);
  assert.equal(state.selectedCard.label, "方向転換");
  assert.equal(state.canConfirm, true);
  assert.deepEqual(state.buildSeedRequest(), { handCardId: "orange_turn" });
});

test("手札に無いカードは選べない", () => {
  const state = ready();
  assert.equal(state.canSelect("green_recover_2"), false);
  assert.equal(state.selectCard("green_recover_2"), false);
  assert.equal(state.selectedCardId, null);
});

test("確定後は選び直しも再送もできない（BR-seed-005）", () => {
  const state = ready();
  state.selectCard("orange_turn");
  state.applyState(payload({ hand: [card("blue_move_3", "移動"), card("yellow_star", "スター")], progress: progress([ME, "p_2"]) }));
  assert.equal(state.seeded, true);
  assert.equal(state.selectedCardId, null, "選択を持ち越さない");
  assert.equal(state.canSelect("blue_move_3"), false);
  assert.equal(state.canConfirm, false);
  assert.equal(state.handCount, 2, "仕込んだ分だけ手札が減る");
});

test("送信中は二重に確定できない", () => {
  const state = ready();
  state.selectCard("orange_turn");
  state.markPending();
  assert.equal(state.canConfirm, false);
  assert.equal(state.buildSeedRequest(), null);
});

test("全員仕込むと揃い扱いになる", () => {
  const state = ready({ progress: progress([ME, "p_2", "p_3", "p_4"]) });
  assert.equal(state.allSeeded, true);
  assert.equal(state.seededCount, 4);
});

test("seed.advanced は一度だけ受け付け、以降の state を無視する", () => {
  const state = ready();
  assert.equal(state.handleMessage("seed.advanced", { phase: "race" }), true);
  assert.equal(state.advanced, true);
  assert.equal(state.canConfirm, false);
  assert.equal(state.handleMessage("seed.state", payload({ raceIndex: 3 })), false);
  assert.equal(state.raceIndex, 2);
});

test("race 以外への advanced は受け付けない", () => {
  const state = ready();
  assert.equal(state.handleMessage("seed.advanced", { phase: "payout" }), false);
  assert.equal(state.advanced, false);
});

test("壊れた payload では状態を進めない", () => {
  const state = ready();
  const broken = [
    payload({ phase: "race" }),
    payload({ raceIndex: 0 }),
    payload({ hand: [card("a", "移動"), card("b", "移動"), card("c", "移動"), card("d", "移動")] }),
    payload({ hand: [card("blue_move_3", "移動"), card("blue_move_3", "移動")] }),
    payload({ hand: [{ cardId: "x", label: "移動", rect: [0, 0, 240] }] }),
    payload({ progress: [{ playerId: ME }] }),
    payload({ deckCountExpected: -1 }),
    "not-json",
  ];
  for (const bad of broken) {
    assert.equal(state.applyState(bad), false);
    assert.equal(state.handCount, 3, "直前の状態を保つ");
    assert.notEqual(state.error, "");
  }
});

test("エラー文言を受け取ったら送信中を解く", () => {
  const state = ready();
  state.selectCard("orange_turn");
  state.markPending();
  state.handleMessage("error", { message: "すでに仕込んでいます" });
  assert.equal(state.pending, false);
  assert.equal(state.error, "すでに仕込んでいます");
});
