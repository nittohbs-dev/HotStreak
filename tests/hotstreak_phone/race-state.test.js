/* SCR-phone-004 / 004b 状態ロジックの検証。node --test で実行する（追加依存なし）。 */
const test = require("node:test");
const assert = require("node:assert/strict");

const { RaceScreenState } = require("../../src/hotstreak_phone/race-state.js");

const ME = "p_1";

function mascot(mascotId, rank, extra) {
  return Object.assign({ mascotId, displayName: mascotId, color: mascotId, rank }, extra || {});
}

function bet(ticketInstanceId, label, face, double) {
  return { ticketInstanceId, label, face, double: Boolean(double) };
}

function player(playerId, rank, balance, bets) {
  return { playerId, displayName: playerId === ME ? "ヤマダ" : playerId, rank, balance, bets: bets || [] };
}

function payload(overrides) {
  return Object.assign(
    {
      phase: "race",
      raceIndex: 2,
      prompt: { text: "コースアウトするマスコットはいる？" },
      mascots: [mascot("blue", 2), mascot("yellow", 1), mascot("salmon", 3), mascot("orange", 4)],
      players: [
        player(ME, 2, 14, [bet("t-1", "ダングル", "risky"), bet("t-2", "サイド YES", "safe", true)]),
        player("p_2", 1, 18, [bet("t-3", "ゴブラー", "safe")]),
      ],
    },
    overrides
  );
}

function ready(overrides) {
  const state = new RaceScreenState(ME);
  assert.equal(state.applyState(payload(overrides)), true);
  return state;
}

test("state を受けるとお題・レース・自分の情報が入る", () => {
  const state = ready();
  assert.equal(state.raceIndex, 2);
  assert.equal(state.prompt.text, "コースアウトするマスコットはいる？");
  assert.equal(state.me.balance, 14);
  assert.equal(state.me.rank, 2);
  assert.equal(state.playerTotal, 2);
  assert.equal(state.myBets.length, 2);
  assert.equal(state.myBets[1].double, true);
});

test("マスコットとプレイヤーはサーバの順位で並べる", () => {
  const state = ready();
  assert.deepEqual(state.rankedMascots.map((m) => m.mascotId), ["yellow", "blue", "salmon", "orange"]);
  assert.deepEqual(state.rankedPlayers.map((p) => p.playerId), ["p_2", ME]);
});

test("ゴールと失格を区別して保つ", () => {
  const state = ready({
    mascots: [
      mascot("yellow", 1, { finished: true }),
      mascot("blue", 2, { finished: true }),
      mascot("salmon", 3),
      mascot("orange", 4, { disqualified: true }),
    ],
  });
  assert.equal(state.rankedMascots[0].finished, true);
  assert.equal(state.rankedMascots[3].disqualified, true);
  assert.equal(state.rankedMascots[2].finished, false);
});

test("全員状況は開閉できる", () => {
  const state = ready();
  assert.equal(state.sheetOpen, false);
  assert.equal(state.openSheet(), true);
  assert.equal(state.sheetOpen, true);
  state.closeSheet();
  assert.equal(state.sheetOpen, false);
});

test("接続前と終了後は全員状況を開かない", () => {
  const before = new RaceScreenState(ME);
  assert.equal(before.openSheet(), false);

  const state = ready();
  state.openSheet();
  state.handleMessage("race.finished", { phase: "payout" });
  assert.equal(state.sheetOpen, false, "終了時に閉じる");
  assert.equal(state.openSheet(), false);
});

test("race.finished は一度だけ受け付け、以降の state を無視する", () => {
  const state = ready();
  assert.equal(state.handleMessage("race.finished", { phase: "payout" }), true);
  assert.equal(state.finished, true);
  assert.equal(state.handleMessage("race.state", payload({ raceIndex: 3 })), false);
  assert.equal(state.raceIndex, 2);
});

test("payout 以外への finished は受け付けない", () => {
  const state = ready();
  assert.equal(state.handleMessage("race.finished", { phase: "card-seed" }), false);
  assert.equal(state.finished, false);
});

test("お題が無くても状態は成立する", () => {
  const state = ready({ prompt: null });
  assert.equal(state.prompt, null);
  assert.equal(state.connected, true);
});

test("壊れた payload では状態を進めない", () => {
  const state = ready();
  const broken = [
    payload({ phase: "payout" }),
    payload({ raceIndex: 4 }),
    payload({ mascots: [mascot("blue", 0)] }),
    payload({ mascots: [mascot("blue", 1), mascot("blue", 2)] }),
    payload({ players: [{ playerId: ME, rank: 1 }] }),
    payload({ players: [player(ME, 1, 10, [bet("t-1", "ダングル", "normal")])] }),
    "not-json",
  ];
  for (const bad of broken) {
    assert.equal(state.applyState(bad), false);
    assert.equal(state.raceIndex, 2, "直前の状態を保つ");
    assert.notEqual(state.error, "");
  }
});

test("エラー文言を受け取って表示に回す", () => {
  const state = ready();
  state.handleMessage("error", { message: "レース中ではありません" });
  assert.equal(state.error, "レース中ではありません");
});
