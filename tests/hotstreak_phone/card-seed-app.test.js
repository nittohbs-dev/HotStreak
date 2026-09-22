/* 画面全体の配線（場面切替・選択・確定）をブラウザ無しで通す。 */
const test = require("node:test");
const assert = require("node:assert/strict");

const fakeDom = require("./fake-dom.js");

const MODULES = {
  HotStreakCardSprite: "../../src/hotstreak_phone/card-sprite.js",
  HotStreakCardSeedState: "../../src/hotstreak_phone/card-seed-state.js",
  HotStreakCardSeedMock: "../../src/hotstreak_phone/card-seed-mock.js",
};
const APP = "../../src/hotstreak_phone/card-seed-app.js";
const VIEW = "../../src/hotstreak_phone/card-seed-view.js";

function boot() {
  const nodes = fakeDom.install();
  for (const [name, path] of Object.entries(MODULES)) {
    delete require.cache[require.resolve(path)];
    globalThis[name] = require(path);
  }
  delete require.cache[require.resolve(VIEW)];
  globalThis.HotStreakCardSeedView = require(VIEW);
  delete require.cache[require.resolve(APP)];
  require(APP);
  return nodes;
}

function statusOf(nodes, index) {
  return nodes["status-list"].children[index].findByClass("seed-player-status").textContent;
}

test("モックは手札3枚と進捗を出して始まる", () => {
  const nodes = boot();
  assert.equal(nodes["demo-bar"].hidden, false);
  assert.equal(nodes["demo-scene"].textContent, "手札3枚・自分は未仕込み");
  assert.equal(nodes["hand-list"].children.length, 3);
  assert.equal(nodes["seed-meta"].textContent, "レース 2/3 ・ 手札 3枚");
  assert.equal(nodes["seed-progress"].textContent, "仕込み 1 / 4 人");
  assert.equal(nodes["confirm-button"].disabled, true);
});

test("選んで確定すると手札が減り、自分が済になる", () => {
  const nodes = boot();
  nodes["hand-list"].children[1].click();
  assert.equal(nodes["hand-list"].children[1].dataset.selected, "true");
  assert.equal(statusOf(nodes, 0), "選択中");
  assert.equal(nodes["confirm-button"].disabled, false);

  nodes["confirm-button"].click();
  assert.equal(nodes["hand-list"].children.length, 2, "仕込んだ1枚が抜ける");
  assert.equal(nodes["seed-meta"].textContent, "レース 2/3 ・ 手札 2枚");
  assert.equal(nodes["seed-progress"].textContent, "仕込み 2 / 4 人");
  assert.equal(statusOf(nodes, 0), "済");
  assert.equal(nodes["seeded-slot"].hidden, false);
  assert.equal(nodes["confirm-button"].hidden, true);
});

test("場面を進めると自分だけ未 → 全員済 → レースへ、と変わる", () => {
  const nodes = boot();
  nodes["demo-next"].click();
  assert.equal(nodes["demo-scene"].textContent, "自分以外は全員仕込み済み");
  assert.equal(nodes["seed-progress"].textContent, "仕込み 3 / 4 人");
  assert.equal(statusOf(nodes, 0), "未");

  nodes["demo-next"].click();
  assert.equal(nodes["demo-scene"].textContent, "全員仕込み済み");
  assert.match(nodes.notice.textContent, /全員そろいました/);

  nodes["demo-next"].click();
  assert.equal(nodes["demo-scene"].textContent, "レースへ進行");
  assert.match(nodes.notice.textContent, /レースがまもなく始まります/);
  assert.equal(nodes["foot-hint"].hidden, true);
});

test("確定後に場面を進めても自分は済のまま", () => {
  const nodes = boot();
  nodes["hand-list"].children[0].click();
  nodes["confirm-button"].click();
  nodes["demo-next"].click();
  assert.equal(statusOf(nodes, 0), "済");
  assert.equal(nodes["seed-progress"].textContent, "仕込み 4 / 4 人");
});
