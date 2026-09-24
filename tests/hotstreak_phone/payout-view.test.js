/* CMP-payout-010〜013 の描画を DOM スタブで検証する。 */
const test = require("node:test");
const assert = require("node:assert/strict");

const fakeDom = require("./fake-dom.js");
const { PayoutScreenState } = require("../../src/hotstreak_phone/payout-state.js");

const ME = "p_1";

function payload(overrides) {
  return Object.assign(
    {
      phase: "payout",
      raceIndex: 1,
      standings: [
        { mascotId: "yellow", displayName: "マム", color: "yellow", rank: 1 },
        { mascotId: "blue", displayName: "ダングル", color: "blue", rank: 2 },
        { mascotId: "salmon", displayName: "ハーレー", color: "salmon", rank: 3 },
        { mascotId: "orange", displayName: "ゴブラー", color: "orange", rank: 4, disqualified: true },
      ],
      balances: [
        { playerId: "p_2", displayName: "サトウ", balance: 25, delta: 8, rank: 1 },
        { playerId: ME, displayName: "ヤマダ", balance: 20, delta: 0, rank: 2 },
        { playerId: "p_4", displayName: "スズキ", balance: 0, delta: -4, rank: 3 },
      ],
      myBreakdown: {
        playerId: ME,
        total: 0,
        items: [
          { ticketInstanceId: "t-1", label: "ダングル", kind: "mascot", face: "safe", tier: "top", amount: 10 },
          { ticketInstanceId: "t-2", label: "サイド NO", kind: "side", face: "risky", tier: "bot", amount: -10, double: true },
        ],
      },
    },
    overrides
  );
}

function setup() {
  const nodes = fakeDom.install();
  delete require.cache[require.resolve("../../src/hotstreak_phone/payout-view.js")];
  const { PayoutView } = require("../../src/hotstreak_phone/payout-view.js");
  return { view: new PayoutView(), nodes };
}

function stateOf(overrides) {
  const state = new PayoutScreenState(ME);
  assert.equal(state.applyState(payload(overrides)), true);
  return state;
}

test("タイトルにレース番号を出す", () => {
  const { view, nodes } = setup();
  view.render(stateOf({ raceIndex: 2 }));
  assert.equal(nodes["payout-title"].textContent, "レース2 結果");
});

test("着順を1位から並べ、失格を示す", () => {
  const { view, nodes } = setup();
  view.render(stateOf());
  const items = nodes["standing-list"].children;
  assert.equal(items.length, 4);
  assert.match(items[0].text, /1位 マム/);
  assert.match(items[3].text, /失格/);
  assert.equal(items[3].dataset.out, "true");
});

test("内訳はダブルを明示し、マイナス額を符号付きで出す", () => {
  const { view, nodes } = setup();
  view.render(stateOf());
  assert.equal(nodes["my-total"].textContent, "$0");
  const rows = nodes["breakdown-list"].children;
  assert.equal(rows.length, 2);
  assert.match(rows[0].text, /ダングル セーフ \+\$10/);
  assert.doesNotMatch(rows[0].text, /ダブル/);
  assert.match(rows[1].text, /★ダブル ×2/);
  assert.match(rows[1].text, /-\$10/);
  assert.equal(rows[1].dataset.double, "true");
  assert.equal(rows[1].findByClass("breakdown-amount").dataset.sign, "-1");
});

test("マ券が無ければ内訳に「マ券なし」を出す", () => {
  const { view, nodes } = setup();
  view.render(stateOf({ myBreakdown: undefined }));
  assert.equal(nodes["my-total"].textContent, "");
  assert.match(nodes["breakdown-list"].children[0].text, /マ券なし/);
});

test("所持金順位で自分を強調し、増減を出す", () => {
  const { view, nodes } = setup();
  view.render(stateOf());
  const rows = nodes["balance-list"].children;
  assert.equal(rows.length, 3);
  assert.equal(rows[1].dataset.self, "true");
  assert.match(rows[1].text, /ヤマダ （自分）/);
  assert.match(rows[0].text, /\$25 \+\$8/);
  assert.match(rows[2].text, /\$0 -\$4/);
  assert.doesNotMatch(nodes["balance-list"].text, /優勝/);
});

test("レース3は優勝者を、同点なら共同優勝を示す", () => {
  const { view, nodes } = setup();
  view.render(stateOf({ raceIndex: 3, winners: ["p_2"] }));
  assert.match(nodes["balance-list"].children[0].text, /優勝/);
  assert.doesNotMatch(nodes["balance-list"].children[0].text, /共同/);

  view.render(stateOf({ raceIndex: 3, winners: ["p_2", ME] }));
  const rows = nodes["balance-list"].children;
  assert.match(rows[0].text, /共同優勝/);
  assert.match(rows[1].text, /共同優勝/);
  assert.equal(rows[2].dataset.winner, "false");
});

test("フッターは Enter 案内、進行後は行き先を出す", () => {
  const { view, nodes } = setup();
  const state = stateOf();
  view.render(state);
  assert.equal(nodes.notice.textContent, "ラズパイ Enter で次のレースへ");

  view.render(stateOf({ raceIndex: 3 }));
  assert.equal(nodes.notice.textContent, "ラズパイ Enter でロビーへ");

  state.handleMessage("payout.advanced", { phase: "betting" });
  view.render(state);
  assert.match(nodes.notice.textContent, /マ券ドラフトへ進みます/);
});

test("受信前は集計中、エラー時はエラー表示にする", () => {
  const { view, nodes } = setup();
  const state = new PayoutScreenState(ME);
  view.render(state);
  assert.match(nodes.notice.textContent, /集計しています/);
  assert.equal(nodes["breakdown-list"].children.length, 0);

  state.applyState({ phase: "race" });
  view.render(state);
  assert.equal(nodes.notice.dataset.error, "true");
});
