/* SCR-phone-002 状態ロジックの検証。node --test で実行する（追加依存なし）。 */
const test = require("node:test");
const assert = require("node:assert/strict");

const { BettingScreenState, HELD_MAX } = require("../../src/hotstreak_phone/betting-state.js");

const ME = "p1";

function ticket(overrides) {
  return Object.assign(
    { ticketId: "mascot-bear", ticketKind: "mascot", label: "くま", tier: "top", remaining: 3 },
    overrides
  );
}

function pick(overrides) {
  return Object.assign(
    {
      ticketInstanceId: "t-1",
      ticketId: "mascot-bear",
      ticketKind: "mascot",
      label: "くま",
      tier: "top",
      face: "safe",
    },
    overrides
  );
}

function payload(overrides) {
  return Object.assign(
    {
      phase: "betting",
      raceIndex: 1,
      round: 1,
      turnIndex: 3,
      turnTotal: 4,
      currentPlayerId: ME,
      prompt: { promptId: "sb-03", text: "コースアウトはある？" },
      stock: [ticket(), ticket({ ticketId: "side-yes", ticketKind: "side", label: "YES", tier: "mid" })],
      players: [
        { playerId: ME, displayName: "ヤマダ" },
        { playerId: "p2", displayName: "サトウ" },
      ],
      picksByPlayer: {},
      doubleByPlayer: {},
    },
    overrides
  );
}

function ready(overrides) {
  const state = new BettingScreenState(ME);
  assert.equal(state.applyState(payload(overrides)), true);
  return state;
}

test("state を受けるとレース・周回・手番が反映される", () => {
  const state = ready();
  assert.equal(state.raceIndex, 1);
  assert.equal(state.round, 1);
  assert.equal(state.turnIndex, 3);
  assert.equal(state.currentPlayerName, "ヤマダ");
  assert.equal(state.isMyTurn, true);
  assert.equal(state.error, "");
});

test("他者の番では札を選べず確定もできない", () => {
  const state = ready({ currentPlayerId: "p2" });
  assert.equal(state.isMyTurn, false);
  assert.equal(state.selectTicket("mascot-bear"), false);
  assert.equal(state.canConfirm, false);
  assert.equal(state.buildPickRequest(), null);
  assert.equal(state.currentPlayerName, "サトウ");
});

test("在庫0の札は選択できない", () => {
  const state = ready({ stock: [ticket({ remaining: 0 })] });
  assert.equal(state.isSoldOut(state.stock[0]), true);
  assert.equal(state.selectTicket("mascot-bear"), false);
  assert.equal(state.canConfirm, false);
});

test("選択はセーフ面から始まり、裏返すとリスキーになる", () => {
  const state = ready();
  assert.equal(state.selectTicket("mascot-bear"), true);
  assert.equal(state.selectedFace, "safe");
  assert.equal(state.toggleFace(), true);
  assert.equal(state.selectedFace, "risky");
  assert.deepEqual(state.buildPickRequest(), {
    ticketKind: "mascot",
    ticketId: "mascot-bear",
    face: "risky",
  });
  assert.equal(state.toggleFace(), true);
  assert.equal(state.selectedFace, "safe");
});

test("face が未確定なら確定できない", () => {
  const state = ready();
  state.selectTicket("mascot-bear");
  state.selectedFace = null;
  assert.equal(state.canConfirm, false);
  assert.equal(state.buildPickRequest(), null);
});

test("送信中は二重に確定できない", () => {
  const state = ready();
  state.selectTicket("mascot-bear");
  assert.equal(state.canConfirm, true);
  state.markPending();
  assert.equal(state.canConfirm, false);
});

test("2枚取得済みならそれ以上選べない", () => {
  const state = ready({
    picksByPlayer: { [ME]: [pick(), pick({ ticketInstanceId: "t-2", ticketId: "side-yes", ticketKind: "side", label: "YES", tier: "mid" })] },
  });
  assert.equal(state.heldCount, HELD_MAX);
  assert.equal(state.selectTicket("mascot-bear"), false);
  assert.equal(state.canConfirm, false);
});

test("レース1–2 ではダブル指定を出さない", () => {
  const state = ready({
    picksByPlayer: { [ME]: [pick(), pick({ ticketInstanceId: "t-2" })] },
  });
  assert.equal(state.isDoubleRace, false);
  assert.equal(state.needsDouble, false);
  assert.equal(state.buildDoubleRequest("t-1"), null);
});

test("第3レースは所持2枚のうち1枚だけダブル指定できる", () => {
  const state = ready({
    raceIndex: 3,
    picksByPlayer: { [ME]: [pick(), pick({ ticketInstanceId: "t-2" })] },
  });
  assert.equal(state.needsDouble, true);
  assert.deepEqual(state.buildDoubleRequest("t-2"), { ticketInstanceId: "t-2" });
  assert.equal(state.buildDoubleRequest("t-9"), null, "所持していない札は指定できない");
});

test("ダブル指定済みなら再指定を求めない", () => {
  const state = ready({
    raceIndex: 3,
    picksByPlayer: { [ME]: [pick(), pick({ ticketInstanceId: "t-2" })] },
    doubleByPlayer: { [ME]: "t-2" },
  });
  assert.equal(state.myDoubleId, "t-2");
  assert.equal(state.needsDouble, false);
});

test("betting.advanced は一度だけ受け付け、以降の state を無視する", () => {
  const state = ready();
  assert.equal(state.handleMessage("betting.advanced", { phase: "card-seed" }), true);
  assert.equal(state.advanced, true);
  assert.equal(state.handleMessage("betting.state", payload({ raceIndex: 2 })), false);
  assert.equal(state.raceIndex, 1);
});

test("card-seed 以外への advanced は受け付けない", () => {
  const state = ready();
  assert.equal(state.handleMessage("betting.advanced", { phase: "race" }), false);
  assert.equal(state.advanced, false);
});

test("壊れた payload では状態を進めない", () => {
  const state = ready();
  const broken = [
    payload({ phase: "card-seed" }),
    payload({ raceIndex: 4 }),
    payload({ stock: [ticket({ remaining: -1 })] }),
    payload({ stock: [ticket({ tier: "unknown" })] }),
    payload({ stock: [ticket(), ticket()] }),
    payload({ picksByPlayer: { [ME]: [pick({ face: "normal" })] } }),
    payload({ picksByPlayer: null }),
    "not-json",
  ];
  for (const bad of broken) {
    assert.equal(state.applyState(bad), false);
    assert.equal(state.raceIndex, 1, "直前の状態を保つ");
    assert.notEqual(state.error, "");
  }
});

test("レース1–2 でダブル指定が付いた state は受け付けない", () => {
  const state = ready();
  const bad = payload({
    raceIndex: 2,
    picksByPlayer: { [ME]: [pick(), pick({ ticketInstanceId: "t-2" })] },
    doubleByPlayer: { [ME]: "t-2" },
  });
  assert.equal(state.applyState(bad), false);
});

test("切断で操作を止め、サーバのエラー文言を表示する", () => {
  const state = ready();
  state.selectTicket("mascot-bear");
  state.markPending();
  state.handleMessage("disconnected", {});
  assert.equal(state.connected, false);
  assert.equal(state.pending, false);
  assert.equal(state.isMyTurn, false);
  assert.equal(state.canConfirm, false);

  state.applyState(payload());
  state.markPending();
  state.handleMessage("error", { message: "あなたの番ではありません" });
  assert.equal(state.pending, false);
  assert.equal(state.error, "あなたの番ではありません");
});

test("手番が他者へ移ると選択を持ち越さない", () => {
  const state = ready();
  state.selectTicket("mascot-bear");
  state.applyState(payload({ currentPlayerId: "p2" }));
  assert.equal(state.selectedTicketId, null);
  assert.equal(state.selectedFace, null);
});
