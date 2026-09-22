/* 画面全体の配線（場面切替・全員状況の開閉）をブラウザ無しで通す。 */
const test = require("node:test");
const assert = require("node:assert/strict");

const fakeDom = require("./fake-dom.js");

const MODULES = {
  HotStreakRaceState: "../../src/hotstreak_phone/race-state.js",
  HotStreakRaceMock: "../../src/hotstreak_phone/race-mock.js",
};
const APP = "../../src/hotstreak_phone/race-app.js";
const VIEW = "../../src/hotstreak_phone/race-view.js";

function boot() {
  const nodes = fakeDom.install();
  for (const [name, path] of Object.entries(MODULES)) {
    delete require.cache[require.resolve(path)];
    globalThis[name] = require(path);
  }
  delete require.cache[require.resolve(VIEW)];
  globalThis.HotStreakRaceView = require(VIEW);
  delete require.cache[require.resolve(APP)];
  require(APP);
  return nodes;
}

test("モックは序盤の順位と自分の情報を出して始まる", () => {
  const nodes = boot();
  assert.equal(nodes["demo-bar"].hidden, false);
  assert.equal(nodes["demo-scene"].textContent, "レース序盤");
  assert.equal(nodes["mascot-rank"].children.length, 4);
  assert.match(nodes["mascot-rank"].children[0].text, /ダングル/);
  assert.equal(nodes["my-bets"].children.length, 2);
  assert.equal(nodes["my-balance"].textContent, "$14");
  assert.equal(nodes["my-rank"].textContent, "2位 / 4人");
});

test("全員の状況を開いて閉じられる", () => {
  const nodes = boot();
  nodes["sheet-button"].click();
  assert.equal(nodes["all-players-sheet"].hidden, false);
  assert.equal(nodes["sheet-list"].children.length, 4);
  assert.match(nodes["sheet-list"].children[0].text, /サトウ/);

  nodes["sheet-close"].click();
  assert.equal(nodes["all-players-sheet"].hidden, true);
});

test("場面を進めると順位が入れ替わり、ゴールと失格が出る", () => {
  const nodes = boot();
  nodes["demo-next"].click();
  assert.equal(nodes["demo-scene"].textContent, "順位が入れ替わる");
  assert.match(nodes["mascot-rank"].children[0].text, /マム/);

  nodes["demo-next"].click();
  assert.equal(nodes["demo-scene"].textContent, "ゴールと失格が出る");
  assert.match(nodes["mascot-rank"].children[0].text, /ゴール/);
  assert.match(nodes["mascot-rank"].children[3].text, /失格/);
});

test("終了すると配当への案内になり、全員の状況を開けない", () => {
  const nodes = boot();
  for (let step = 0; step < 3; step += 1) nodes["demo-next"].click();
  assert.equal(nodes["demo-scene"].textContent, "レース終了（配当へ）");
  assert.match(nodes.notice.textContent, /配当へ進みます/);
  assert.equal(nodes["sheet-button"].disabled, true);

  nodes["sheet-button"].click();
  assert.equal(nodes["all-players-sheet"].hidden, true);
});
