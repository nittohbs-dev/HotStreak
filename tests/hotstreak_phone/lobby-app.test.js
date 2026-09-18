/* 画面全体の配線（参加・確定・待機・マ券画面への引き渡し）をブラウザ無しで通す。 */
const test = require("node:test");
const assert = require("node:assert/strict");

const fakeDom = require("./fake-dom.js");

const MODULES = {
  HotStreakLobbyState: "../../src/hotstreak_phone/lobby-state.js",
  HotStreakLobbyConnection: "../../src/hotstreak_phone/lobby-connection.js",
  HotStreakLobbyDemo: "../../src/hotstreak_phone/lobby-demo.js",
};
const APP = "../../src/hotstreak_phone/lobby-app.js";
const VIEW = "../../src/hotstreak_phone/lobby-view.js";

function boot(search) {
  const nodes = fakeDom.install();
  const visited = [];
  globalThis.location = { search, assign: (url) => visited.push(url) };
  globalThis.window = { addEventListener() {} };
  for (const [name, path] of Object.entries(MODULES)) globalThis[name] = require(path);
  delete require.cache[require.resolve(VIEW)];
  globalThis.HotStreakLobbyView = require(VIEW);
  delete require.cache[require.resolve(APP)];
  require(APP);
  return { nodes, visited };
}

test("デモは参加済みの状態で開き、自分の行を出す", () => {
  const { nodes } = boot("?demo=1");
  assert.equal(nodes["demo-bar"].hidden, false);
  assert.equal(nodes["player-count"].textContent, "参加者 4 人");
  assert.equal(nodes["player-list"].children.length, 4);
  assert.match(nodes["player-list"].children[0].text, /（自分）/);
  assert.equal(nodes["confirm-button"].disabled, true, "未入力では確定できない");
});

test("デモで名前を入力して確定すると入力済になる", () => {
  const { nodes } = boot("?demo=1");
  nodes["name-input"].type("ヤマダ");
  assert.equal(nodes["confirm-button"].disabled, false);

  nodes["confirm-button"].click();
  const me = nodes["player-list"].children[0];
  assert.match(me.text, /ヤマダ/);
  assert.match(me.findByClass("player-status").textContent, /入力済/);
  assert.equal(nodes["name-input"].disabled, true);
});

test("デモで名前を入れずに進むと、付いた名前が画面に出る", () => {
  const { nodes } = boot("?demo=1");
  nodes["demo-next"].click();
  nodes["demo-next"].click();
  nodes["demo-next"].click();
  assert.equal(nodes["demo-scene"].textContent, "公開カードの準備中");
  assert.match(nodes["player-list"].children[0].text, /プレイヤー1/);
  assert.match(nodes.notice.textContent, /名前は「プレイヤー1」で決まりました/);
});

test("デモで全員そろい、進行するとマ券画面へ移る", () => {
  const { nodes, visited } = boot("?demo=1");
  nodes["name-input"].type("ヤマダ");
  nodes["confirm-button"].click();

  nodes["demo-next"].click();
  nodes["demo-next"].click();
  assert.equal(nodes["demo-scene"].textContent, "ほかの人は全員入力済");
  assert.match(nodes.notice.textContent, /全員そろいました/);

  nodes["demo-next"].click();
  assert.match(nodes.notice.textContent, /公開カードの準備中/);
  assert.deepEqual(visited, []);

  nodes["demo-next"].click();
  assert.deepEqual(visited, ["betting.html?demo=1"]);
});

test("session が無ければ接続せず案内を出す", () => {
  const { nodes } = boot("");
  assert.equal(nodes.notice.dataset.error, "true");
  assert.match(nodes.notice.textContent, /session を URL に付けて/);
  assert.equal(nodes["confirm-button"].disabled, true);
});

test("不正な server 指定はその場で案内する", () => {
  const { nodes } = boot("?session=s1&server=ftp://example.test");
  assert.equal(nodes.notice.dataset.error, "true");
  assert.match(nodes.notice.textContent, /http\(s\)/);
});
