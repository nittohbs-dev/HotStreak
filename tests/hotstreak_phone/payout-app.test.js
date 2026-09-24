/* 画面全体の配線（場面切替）をブラウザ無しで通す。 */
const test = require("node:test");
const assert = require("node:assert/strict");

const fakeDom = require("./fake-dom.js");

const MODULES = {
  HotStreakTicketPayouts: "../../src/hotstreak_phone/ticket-payouts.js",
  HotStreakPayoutState: "../../src/hotstreak_phone/payout-state.js",
  HotStreakPayoutMock: "../../src/hotstreak_phone/payout-mock.js",
};
const APP = "../../src/hotstreak_phone/payout-app.js";
const VIEW = "../../src/hotstreak_phone/payout-view.js";

function boot() {
  const nodes = fakeDom.install();
  for (const [name, path] of Object.entries(MODULES)) {
    delete require.cache[require.resolve(path)];
    globalThis[name] = require(path);
  }
  delete require.cache[require.resolve(VIEW)];
  globalThis.HotStreakPayoutView = require(VIEW);
  delete require.cache[require.resolve(APP)];
  require(APP);
  return nodes;
}

test("モックはレース1結果から始まる", () => {
  const nodes = boot();
  assert.equal(nodes["demo-bar"].hidden, false);
  assert.equal(nodes["demo-scene"].textContent, "レース1結果");
  assert.equal(nodes["payout-title"].textContent, "レース1 結果");
  assert.equal(nodes["standing-list"].children.length, 4);
  assert.equal(nodes["my-total"].textContent, "-$2");
  assert.equal(nodes["balance-list"].children.length, 4);
  assert.equal(nodes["balance-list"].children[3].dataset.self, "true");
});

test("場面を進めるとレース3結果・共同優勝・Enter 後になる", () => {
  const nodes = boot();
  nodes["demo-next"].click();
  assert.equal(nodes["demo-scene"].textContent, "レース3結果");
  assert.match(nodes["breakdown-list"].text, /★ダブル ×2/);
  assert.match(nodes["balance-list"].children[0].text, /サトウ 優勝/);

  nodes["demo-next"].click();
  assert.equal(nodes["demo-scene"].textContent, "レース3・共同優勝");
  assert.match(nodes["balance-list"].children[1].text, /共同優勝/);

  nodes["demo-next"].click();
  assert.equal(nodes["demo-scene"].textContent, "Enter 後（ロビーへ）");
  assert.match(nodes.notice.textContent, /ロビーに戻ります/);
});

test("最後の場面から最初に戻せる", () => {
  const nodes = boot();
  for (let step = 0; step < 4; step += 1) nodes["demo-next"].click();
  assert.equal(nodes["demo-scene"].textContent, "レース1結果");
  assert.equal(nodes["payout-title"].textContent, "レース1 結果");
  assert.equal(nodes.notice.textContent, "ラズパイ Enter で次のレースへ");
});
