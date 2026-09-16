/* 画面全体の配線（起動・デモ・確定）をブラウザ無しで通す。 */
const test = require("node:test");
const assert = require("node:assert/strict");

const fakeDom = require("./fake-dom.js");

const MODULES = {
  HotStreakTicketPayouts: "../../src/hotstreak_phone/ticket-payouts.js",
  HotStreakBettingState: "../../src/hotstreak_phone/betting-state.js",
  HotStreakBettingConnection: "../../src/hotstreak_phone/betting-connection.js",
  HotStreakBettingDemo: "../../src/hotstreak_phone/betting-demo.js",
};
const APP = "../../src/hotstreak_phone/betting-app.js";
const VIEW = "../../src/hotstreak_phone/betting-view.js";

function boot(search) {
  const nodes = fakeDom.install();
  globalThis.location = { search };
  globalThis.window = { addEventListener() {} };
  for (const [name, path] of Object.entries(MODULES)) globalThis[name] = require(path);
  delete require.cache[require.resolve(VIEW)];
  globalThis.HotStreakBettingView = require(VIEW);
  delete require.cache[require.resolve(APP)];
  require(APP);
  return nodes;
}

test("デモモードは最初の場面を描画し、デモ操作バーを出す", () => {
  const nodes = boot("?demo=1");
  assert.equal(nodes["demo-bar"].hidden, false);
  assert.equal(nodes["demo-scene"].textContent, "他の人の番");
  assert.equal(nodes["turn-status"].textContent, "サトウ の番です");
  assert.equal(nodes["ticket-list"].children.length, 6);
  assert.equal(nodes["confirm-button"].disabled, true);
});

test("デモで札を選び、裏返して確定すると所持に入る", () => {
  const nodes = boot("?demo=1");
  nodes["demo-next"].click();
  assert.equal(nodes["demo-scene"].textContent, "自分の番・所持0");
  assert.equal(nodes["turn-status"].textContent, "あなたの番です");

  const bear = nodes["ticket-list"].children[0];
  bear.click();
  assert.equal(nodes["ticket-list"].children[0].dataset.selected, "true");
  assert.equal(nodes["confirm-button"].disabled, false);

  nodes["ticket-list"].children[0].findByClass("flip").click();
  assert.match(nodes["ticket-list"].children[0].text, /リスキー/);

  nodes["confirm-button"].click();
  assert.match(nodes["held-tickets"].children[0].text, /くま/);
  assert.match(nodes["held-tickets"].children[0].text, /リスキー/);
  assert.equal(nodes["held-tickets"].children[1].textContent, "空き");
  assert.match(nodes["ticket-list"].children[0].text, /残り 2枚/, "在庫が1枚減る");
});

test("デモの第3レース場面でダブル指定ができる", () => {
  const nodes = boot("?demo=1");
  for (let step = 0; step < 3; step += 1) nodes["demo-next"].click();
  assert.equal(nodes["demo-scene"].textContent, "第3レース・ダブル指定");
  assert.equal(nodes["double-picker"].hidden, false);

  nodes["double-slots"].children[1].click();
  assert.equal(nodes["double-picker"].hidden, true, "指定後は再指定を求めない");
  assert.match(nodes["held-tickets"].children[1].text, /★ダブル/);
});

test("session と player が無ければ接続せず案内を出す", () => {
  const nodes = boot("");
  assert.equal(nodes["turn-status"].textContent, "接続できません");
  assert.equal(nodes.notice.dataset.error, "true");
  assert.match(nodes.notice.textContent, /session と player/);
});

test("不正な server 指定はその場で案内する", () => {
  const nodes = boot("?session=s1&player=p1&server=ftp://example.test");
  assert.equal(nodes["turn-status"].textContent, "接続できません");
  assert.match(nodes.notice.textContent, /http\(s\)/);
});
