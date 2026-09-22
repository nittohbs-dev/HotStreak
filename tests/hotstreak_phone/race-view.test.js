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

test("お題とレース番号を出す", () => {
  const { view, nodes } = setup();
  view.render(stateOf());
  assert.equal(nodes["race-meta"].textContent, "レース 2/3");
  assert.equal(nodes["side-prompt"].textContent, "コースアウトするマスコットはいる？");
  assert.equal(nodes["side-prompt"].hidden, false);
});

test("お題が無ければ帯を隠す", () => {
  const { view, nodes } = setup();
  view.render(stateOf({ prompt: null }));
  assert.equal(nodes["side-prompt"].hidden, true);
});

test("マスコットを順位順に並べ、ゴールと失格を示す", () => {
  const { view, nodes } = setup();
  view.render(
    stateOf({
      mascots: [
        mascot("yellow", "マム", 1, { finished: true }),
        mascot("blue", "ダングル", 2),
        mascot("salmon", "ハーレー", 3),
        mascot("orange", "ゴブラー", 4, { disqualified: true }),
      ],
    })
  );
  const rows = nodes["mascot-rank"].children;
  assert.equal(rows.length, 4);
  assert.match(rows[0].text, /1位/);
  assert.match(rows[0].text, /マム/);
  assert.match(rows[0].text, /ゴール/);
  assert.equal(rows[3].dataset.out, "true");
  assert.match(rows[3].text, /失格/);
  assert.equal(rows[1].findByClass("mascot-note"), null, "進行中は注記を出さない");
});

test("自分のマ券・所持金・順位を出す", () => {
  const { view, nodes } = setup();
  view.render(stateOf());
  const chips = nodes["my-bets"].children;
  assert.equal(chips.length, 2);
  assert.match(chips[0].text, /ダングル/);
  assert.match(chips[0].text, /リスキー/);
  assert.match(chips[1].text, /★ダブル/);
  assert.equal(nodes["my-balance"].textContent, "$14");
  assert.equal(nodes["my-rank"].textContent, "2位 / 2人");
});

test("マ券が無ければ空の印を出す", () => {
  const { view, nodes } = setup();
  view.render(
    stateOf({
      players: [{ playerId: ME, displayName: "ヤマダ", rank: 1, balance: 0, bets: [] }],
    })
  );
  assert.match(nodes["my-bets"].children[0].textContent, /マ券なし/);
  assert.equal(nodes["my-balance"].textContent, "$0");
});

test("全員の状況ボタンで開閉を通知する", () => {
  const { view, nodes, calls } = setup();
  view.render(stateOf());
  assert.equal(nodes["all-players-sheet"].hidden, true);
  nodes["sheet-button"].click();
  nodes["sheet-close"].click();
  assert.deepEqual(calls, [["open"], ["close"]]);
});

test("全員の状況には各プレイヤーの札を出す", () => {
  const { view, nodes } = setup();
  const state = stateOf();
  state.openSheet();
  view.render(state);
  assert.equal(nodes["all-players-sheet"].hidden, false);
  const rows = nodes["sheet-list"].children;
  assert.equal(rows.length, 2);
  assert.match(rows[0].text, /サトウ/, "順位順に並べる");
  assert.equal(rows[1].dataset.self, "true");
  assert.match(rows[1].text, /（自分）/);
  assert.match(rows[1].text, /サイド YES/);
});

test("終了すると配当への案内を出し、全員の状況を閉じる", () => {
  const { view, nodes } = setup();
  const state = stateOf();
  state.openSheet();
  state.handleMessage("race.finished", { phase: "payout" });
  view.render(state);
  assert.equal(nodes["all-players-sheet"].hidden, true);
  assert.equal(nodes["sheet-button"].disabled, true);
  assert.match(nodes.notice.textContent, /配当へ進みます/);
});

test("エラーは赤字で出す", () => {
  const { view, nodes } = setup();
  const state = stateOf();
  state.handleMessage("error", { message: "レース中ではありません" });
  view.render(state);
  assert.equal(nodes.notice.textContent, "レース中ではありません");
  assert.equal(nodes.notice.dataset.error, "true");
});
