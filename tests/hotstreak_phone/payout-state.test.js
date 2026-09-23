/* CLS-payout-011 の状態部。受信の検証・並び順・共同優勝・Enter 後の凍結を確認する。 */
const test = require("node:test");
const assert = require("node:assert/strict");

const { PayoutScreenState, MESSAGES } = require("../../src/hotstreak_phone/payout-state.js");

const ME = "p_1";

function standing(mascotId, displayName, rank, extra) {
  return Object.assign({ mascotId, displayName, color: mascotId, rank }, extra || {});
}

function payload(overrides) {
  return Object.assign(
    {
      phase: "payout",
      raceIndex: 1,
      standings: [
        standing("salmon", "ハーレー", 3),
        standing("yellow", "マム", 1),
        standing("orange", "ゴブラー", 4, { disqualified: true }),
        standing("blue", "ダングル", 2),
      ],
      balances: [
        { playerId: ME, displayName: "ヤマダ", balance: 8, delta: -2, rank: 2 },
        { playerId: "p_2", displayName: "サトウ", balance: 17, delta: 7, rank: 1 },
      ],
      myBreakdown: {
        playerId: ME,
        total: -2,
        items: [
          { ticketInstanceId: "t-1", label: "ダングル", kind: "mascot", face: "risky", tier: "mid", amount: 3 },
          { ticketInstanceId: "t-2", label: "サイド YES", kind: "side", face: "risky", tier: "top", amount: -5, double: true },
        ],
      },
    },
    overrides
  );
}

function applied(overrides) {
  const state = new PayoutScreenState(ME);
  assert.equal(state.applyState(payload(overrides)), true);
  return state;
}

test("正しい payout.state を反映する", () => {
  const state = applied();
  assert.equal(state.connected, true);
  assert.equal(state.raceIndex, 1);
  assert.equal(state.me.balance, 8);
  assert.equal(state.playerTotal, 2);
  assert.equal(state.breakdown.total, -2);
  assert.equal(state.breakdown.items[1].double, true);
  assert.equal(state.breakdown.items[0].double, false);
});

test("着順と所持金順位はサーバの rank で並べる", () => {
  const state = applied();
  assert.deepEqual(state.rankedStandings.map((m) => m.mascotId), ["yellow", "blue", "salmon", "orange"]);
  assert.equal(state.rankedStandings[3].disqualified, true);
  assert.deepEqual(state.rankedBalances.map((p) => p.playerId), ["p_2", ME]);
});

test("内訳が無い（マ券なし）場合は null で受ける", () => {
  const state = applied({ myBreakdown: undefined });
  assert.equal(state.breakdown, null);
});

const BROKEN = {
  "フェーズ違い": { phase: "race" },
  "レース番号の範囲外": { raceIndex: 4 },
  "マスコットの重複": { standings: [standing("blue", "ダングル", 1), standing("blue", "ダングル", 2)] },
  "プレイヤーの重複": {
    balances: [
      { playerId: ME, balance: 1, delta: 0, rank: 1 },
      { playerId: ME, balance: 2, delta: 0, rank: 2 },
    ],
  },
  "所持金がマイナス": { balances: [{ playerId: ME, balance: -1, delta: -3, rank: 1 }] },
  "他人の内訳": { myBreakdown: { playerId: "p_2", total: 0, items: [] } },
  "内訳の札種別が不正": {
    myBreakdown: { playerId: ME, total: 1, items: [{ ticketInstanceId: "t", label: "x", kind: "?", face: "safe", tier: "top", amount: 1 }] },
  },
  "勝者が参加者にいない": { raceIndex: 3, winners: ["p_9"] },
};

for (const [name, overrides] of Object.entries(BROKEN)) {
  test(`壊れた payload を拒否して状態を進めない: ${name}`, () => {
    const state = applied();
    assert.equal(state.applyState(payload(overrides)), false);
    assert.equal(state.error, MESSAGES.invalidState);
    assert.equal(state.raceIndex, 1);
    assert.equal(state.me.balance, 8);
  });
}

test("オブジェクトでない payload は拒否する", () => {
  const state = new PayoutScreenState(ME);
  assert.equal(state.applyState(null), false);
  assert.equal(state.connected, false);
});

test("レース3で同点最多は共同優勝として複数の勝者を持つ", () => {
  const state = applied({ raceIndex: 3, winners: ["p_2", ME] });
  assert.equal(state.isFinalRace, true);
  assert.equal(state.isWinner(ME), true);
  assert.equal(state.isWinner("p_2"), true);
});

test("レース1–2では勝者を扱わない", () => {
  const state = applied({ winners: [ME] });
  assert.equal(state.isWinner(ME), false);
});

test("payout.advanced の後は以降の受信を無視する", () => {
  const state = applied();
  assert.equal(state.handleMessage("payout.advanced", { phase: "betting" }), true);
  assert.equal(state.advancedTo, "betting");
  assert.equal(state.handleMessage("payout.state", payload({ raceIndex: 2 })), false);
  assert.equal(state.raceIndex, 1);
});

test("行き先が不正な payout.advanced は無視する", () => {
  const state = applied();
  assert.equal(state.handleMessage("payout.advanced", { phase: "race" }), false);
  assert.equal(state.advancedTo, "");
});

test("error はサーバの文言を出し、無ければ既定文言にする", () => {
  const state = applied();
  state.handleMessage("error", { message: "この操作はできません" });
  assert.equal(state.error, "この操作はできません");
  state.handleMessage("error", {});
  assert.equal(state.error, MESSAGES.invalidState);
  state.handleMessage("payout.state", payload());
  assert.equal(state.error, "");
});
