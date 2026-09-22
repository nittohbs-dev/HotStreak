/* CMP-seed-011〜013 の描画を DOM スタブで検証する。 */
const test = require("node:test");
const assert = require("node:assert/strict");

const fakeDom = require("./fake-dom.js");
const { CardSeedScreenState } = require("../../src/hotstreak_phone/card-seed-state.js");

const ME = "p_1";

function card(cardId, label, rect) {
  return { cardId, label, color: "blue", rect: rect || [0, 0, 240, 336] };
}

function progress(seededIds) {
  return [
    { playerId: ME, displayName: "ヤマダ", seeded: seededIds.includes(ME) },
    { playerId: "p_2", displayName: "サトウ", seeded: seededIds.includes("p_2") },
    { playerId: "p_3", displayName: "タナカ", seeded: seededIds.includes("p_3") },
  ];
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

function setup() {
  const nodes = fakeDom.install();
  for (const path of ["../../src/hotstreak_phone/card-sprite.js", "../../src/hotstreak_phone/card-seed-view.js"]) {
    delete require.cache[require.resolve(path)];
  }
  globalThis.HotStreakCardSprite = require("../../src/hotstreak_phone/card-sprite.js");
  const { CardSeedView } = require("../../src/hotstreak_phone/card-seed-view.js");
  const calls = [];
  const view = new CardSeedView({
    onSelect: (cardId) => calls.push(["select", cardId]),
    onConfirm: () => calls.push(["confirm"]),
  });
  return { view, nodes, calls };
}

function stateOf(overrides) {
  const state = new CardSeedScreenState(ME);
  assert.equal(state.applyState(payload(overrides)), true);
  return state;
}

test("レース・手札枚数・仕込み進捗を出す", () => {
  const { view, nodes } = setup();
  view.render(stateOf());
  assert.equal(nodes["seed-meta"].textContent, "レース 2/3 ・ 手札 3枚");
  assert.equal(nodes["seed-progress"].textContent, "仕込み 1 / 3 人");
});

test("手札をカード絵とラベルで並べる", () => {
  const { view, nodes } = setup();
  view.render(stateOf());
  const cards = nodes["hand-list"].children;
  assert.equal(cards.length, 3);
  assert.equal(cards[0].findByClass("card-art").tag, "div", "カード絵の枠を持つ");
  assert.equal(cards[0].findByTag("img").src, "../../assets/images/cards/cards_atlas.png");
  assert.match(cards[1].findByClass("hand-label").textContent, /方向転換/);
});

test("タップで選択を通知し、選んだ札を強調する", () => {
  const { view, nodes, calls } = setup();
  const state = stateOf();
  view.render(state);
  nodes["hand-list"].children[1].click();
  assert.deepEqual(calls, [["select", "orange_turn"]]);

  state.selectCard("orange_turn");
  view.render(state);
  assert.equal(nodes["hand-list"].children[1].dataset.selected, "true");
  assert.equal(nodes["hand-list"].children[0].dataset.selected, "false");
  assert.equal(nodes["confirm-button"].disabled, false);
});

test("未選択のうちは確定できず、選ぶよう促す", () => {
  const { view, nodes } = setup();
  view.render(stateOf());
  assert.equal(nodes["confirm-button"].disabled, true);
  assert.match(nodes.notice.textContent, /1枚選んでください/);
});

test("確定後は裏面を出し、手札をタップしても選択が走らない", () => {
  const { view, nodes, calls } = setup();
  const state = stateOf({
    hand: [card("blue_move_3", "移動"), card("yellow_star", "スター")],
    progress: progress([ME, "p_2"]),
  });
  view.render(state);
  assert.equal(nodes["seeded-slot"].hidden, false);
  assert.match(nodes["seeded-slot"].text, /仕込み済み/);
  assert.equal(nodes["hand-list"].children[0].dataset.locked, "true");
  nodes["hand-list"].children[0].click();
  assert.deepEqual(calls, []);
  assert.equal(nodes["confirm-button"].hidden, true);
  assert.match(nodes.notice.textContent, /変更できません/);
});

test("仕込み状況に自分と済／未を出す", () => {
  const { view, nodes } = setup();
  const state = stateOf();
  view.render(state);
  const rows = nodes["status-list"].children;
  assert.equal(rows[0].dataset.self, "true");
  assert.match(rows[0].text, /（自分）/);
  assert.equal(rows[0].findByClass("seed-player-status").textContent, "未");
  assert.equal(rows[1].findByClass("seed-player-status").textContent, "済");

  state.selectCard("orange_turn");
  view.render(state);
  assert.equal(nodes["status-list"].children[0].findByClass("seed-player-status").textContent, "選択中");
});

test("全員そろったら束の枚数を案内する", () => {
  const { view, nodes } = setup();
  view.render(stateOf({ hand: [], progress: progress([ME, "p_2", "p_3"]) }));
  assert.match(nodes.notice.textContent, /全員そろいました/);
  assert.match(nodes.notice.textContent, /18 枚/);
});

test("進行後は確定ボタンと案内を隠す", () => {
  const { view, nodes } = setup();
  const state = stateOf();
  state.handleMessage("seed.advanced", { phase: "race" });
  view.render(state);
  assert.equal(nodes["confirm-button"].hidden, true);
  assert.equal(nodes["foot-hint"].hidden, true);
  assert.match(nodes.notice.textContent, /レースがまもなく始まります/);
});

test("エラーは赤字で出す", () => {
  const { view, nodes } = setup();
  const state = stateOf();
  state.handleMessage("error", { message: "そのカードは選べません" });
  view.render(state);
  assert.equal(nodes.notice.textContent, "そのカードは選べません");
  assert.equal(nodes.notice.dataset.error, "true");
});
