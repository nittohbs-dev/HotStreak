/* CMP-betting-011〜014 の描画を DOM スタブで検証する。ブラウザ描画の代替ではなく回帰検出用。 */
const test = require("node:test");
const assert = require("node:assert/strict");

globalThis.HotStreakTicketPayouts = require("../../src/hotstreak_phone/ticket-payouts.js");
const { BettingScreenState } = require("../../src/hotstreak_phone/betting-state.js");
const fakeDom = require("./fake-dom.js");

function setup() {
  const registry = fakeDom.install();
  delete require.cache[require.resolve("../../src/hotstreak_phone/betting-view.js")];
  const { BettingView } = require("../../src/hotstreak_phone/betting-view.js");
  const calls = [];
  const view = new BettingView({
    onSelect: (id) => calls.push(["select", id]),
    onToggleFace: () => calls.push(["toggle"]),
    onConfirm: () => calls.push(["confirm"]),
    onDouble: (id) => calls.push(["double", id]),
  });
  return { view, nodes: registry, calls };
}

function payload(overrides) {
  return Object.assign(
    {
      phase: "betting",
      raceIndex: 1,
      round: 2,
      turnIndex: 3,
      turnTotal: 4,
      currentPlayerId: "p1",
      prompt: { promptId: "sb-01", text: "コースアウトはある？" },
      stock: [
        { ticketId: "mascot-bear", ticketKind: "mascot", label: "くま", tier: "top", remaining: 2 },
        { ticketId: "side-yes", ticketKind: "side", label: "サイド YES", tier: "top", remaining: 0 },
      ],
      players: [
        { playerId: "p1", displayName: "ヤマダ" },
        { playerId: "p2", displayName: "サトウ" },
      ],
      picksByPlayer: {},
      doubleByPlayer: {},
    },
    overrides
  );
}

function stateOf(overrides) {
  const state = new BettingScreenState("p1");
  assert.equal(state.applyState(payload(overrides)), true);
  return state;
}

test("自分の番では手番バー・周回・レース・お題を表示する", () => {
  const { view, nodes } = setup();
  view.render(stateOf());
  assert.equal(nodes["turn-status"].textContent, "あなたの番です");
  assert.equal(nodes["turn-status"].dataset.mode, "mine");
  assert.equal(nodes["turn-detail"].textContent, "2周目 3/4");
  assert.equal(nodes["race-meta"].textContent, "レース 1/3");
  assert.equal(nodes["side-prompt"].textContent, "コースアウトはある？");
});

test("他者の番は名前を出し、操作できない案内を表示する", () => {
  const { view, nodes } = setup();
  view.render(stateOf({ currentPlayerId: "p2" }));
  assert.equal(nodes["turn-status"].textContent, "サトウ の番です");
  assert.equal(nodes["confirm-button"].disabled, true);
  assert.match(nodes.notice.textContent, /ほかの人の番/);
});

test("在庫0の札は無効表示にし、タップしても選択が走らない", () => {
  const { view, nodes, calls } = setup();
  view.render(stateOf());
  const [bear, yes] = nodes["ticket-list"].children;
  assert.equal(bear.dataset.soldOut, "false");
  assert.equal(yes.dataset.soldOut, "true");
  assert.match(yes.text, /残り 0枚（選べません）/);
  yes.click();
  assert.deepEqual(calls, []);
  bear.click();
  assert.deepEqual(calls, [["select", "mascot-bear"]]);
});

test("選択中の札は配当と裏返しボタンを出す", () => {
  const { view, nodes, calls } = setup();
  const state = stateOf();
  state.selectTicket("mascot-bear");
  view.render(state);
  const bear = nodes["ticket-list"].children[0];
  assert.equal(bear.dataset.selected, "true");
  assert.match(bear.text, /セーフ/);
  assert.match(bear.text, /1着 \$10・2着 \$7・3着 \$5/);
  const flip = bear.findByClass("flip");
  assert.match(flip.textContent, /裏返す → リスキー/);
  flip.click();
  assert.deepEqual(calls, [["toggle"]]);
  assert.equal(nodes["confirm-button"].disabled, false);
});

test("裏返すとリスキーの配当に切り替わる", () => {
  const { view, nodes } = setup();
  const state = stateOf();
  state.selectTicket("mascot-bear");
  state.toggleFace();
  view.render(state);
  const bear = nodes["ticket-list"].children[0];
  assert.match(bear.text, /リスキー/);
  assert.match(bear.text, /1着 \$15・2着 \$5・3着 \$2/);
});

test("所持は常に2枠で、空き枠を見せる", () => {
  const { view, nodes } = setup();
  const state = stateOf({
    picksByPlayer: {
      p1: [
        {
          ticketInstanceId: "t-1",
          ticketId: "mascot-bear",
          ticketKind: "mascot",
          label: "くま",
          tier: "top",
          face: "risky",
        },
      ],
    },
  });
  view.render(state);
  const slots = nodes["held-tickets"].children;
  assert.equal(slots.length, 2);
  assert.match(slots[0].text, /くま/);
  assert.match(slots[0].text, /リスキー/);
  assert.equal(slots[1].textContent, "空き");
});

test("レース1–2 ではダブル指定を隠す", () => {
  const { view, nodes } = setup();
  view.render(stateOf());
  assert.equal(nodes["double-picker"].hidden, true);
});

test("第3レースは所持2枚をダブル候補として出す", () => {
  const { view, nodes, calls } = setup();
  const picks = [
    { ticketInstanceId: "t-1", ticketId: "mascot-bear", ticketKind: "mascot", label: "くま", tier: "top", face: "safe" },
    { ticketInstanceId: "t-2", ticketId: "side-yes", ticketKind: "side", label: "サイド YES", tier: "top", face: "risky" },
  ];
  view.render(stateOf({ raceIndex: 3, picksByPlayer: { p1: picks } }));
  assert.equal(nodes["double-picker"].hidden, false);
  const options = nodes["double-slots"].children;
  assert.equal(options.length, 2);
  assert.equal(options[1].textContent, "サイド YES（リスキー）");
  options[1].click();
  assert.deepEqual(calls, [["double", "t-2"]]);
  assert.match(nodes.notice.textContent, /ダブルにする札/);
});

test("送信中は確定ボタンを止める", () => {
  const { view, nodes } = setup();
  const state = stateOf();
  state.selectTicket("mascot-bear");
  state.markPending();
  view.render(state);
  assert.equal(nodes["confirm-button"].disabled, true);
  assert.equal(nodes["confirm-button"].textContent, "送信中…");
});

test("切断と進行を案内する", () => {
  const { view, nodes } = setup();
  const state = stateOf();
  state.handleMessage("disconnected", {});
  view.render(state);
  assert.equal(nodes["turn-status"].textContent, "接続中…");
  assert.equal(nodes.notice.dataset.error, "true");

  state.applyState(payload());
  state.handleMessage("betting.advanced", { phase: "card-seed" });
  view.render(state);
  assert.equal(nodes["turn-status"].textContent, "カード仕込みへ進みます");
  assert.equal(nodes["confirm-button"].disabled, true);
});

test("確定ボタンの押下を通知する", () => {
  const { nodes, calls } = setup();
  nodes["confirm-button"].click();
  assert.deepEqual(calls, [["confirm"]]);
});
