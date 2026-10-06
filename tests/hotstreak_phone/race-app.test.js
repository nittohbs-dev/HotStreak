/* 画面全体の配線をブラウザ無しで通す。 */
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

test("モックはお題と購入したマ券を出して始まる", () => {
  const nodes = boot();
  assert.equal(nodes["demo-bar"].hidden, false);
  assert.equal(nodes["demo-scene"].textContent, "レース序盤");
  assert.match(nodes["side-prompt"].textContent, /コースアウト/);
  assert.equal(nodes["my-bets"].children.length, 2);
  assert.match(nodes["my-bets"].children[0].text, /ダングル/);
  assert.match(nodes["my-bets"].children[1].text, /サイド YES/);
});

test("レースの場面が進んでもお題と購入マ券を保つ", () => {
  const nodes = boot();
  nodes["demo-next"].click();
  assert.equal(nodes["demo-scene"].textContent, "順位が入れ替わる");
  assert.match(nodes["side-prompt"].textContent, /コースアウト/);
  assert.equal(nodes["my-bets"].children.length, 2);
});
