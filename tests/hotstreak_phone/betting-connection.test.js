/* API-BETTING-002/003 のエラー文言と WS 封筒の取り扱いを検証する。 */
const test = require("node:test");
const assert = require("node:assert/strict");

const { BettingConnection, OFFLINE } = require("../../src/hotstreak_phone/betting-connection.js");

function connect(onMessage) {
  return new BettingConnection({
    server: "http://127.0.0.1:8000",
    sessionId: "S 1",
    playerId: "p1",
    onMessage: onMessage || (() => {}),
  });
}

function response(status, body) {
  return {
    ok: status < 400,
    status,
    json: async () => body,
  };
}

test("エンドポイントを設計どおりに組み立て、sessionId をエスケープする", () => {
  const connection = connect();
  assert.equal(connection.urls.state, "http://127.0.0.1:8000/api/sessions/S%201/betting");
  assert.equal(connection.urls.picks, "http://127.0.0.1:8000/api/sessions/S%201/betting/picks");
  assert.equal(connection.urls.double, "http://127.0.0.1:8000/api/sessions/S%201/betting/double");
  assert.equal(connection.urls.ws, "ws://127.0.0.1:8000/ws/sessions/S%201");
});

test("https は wss になる", () => {
  const connection = new BettingConnection({
    server: "https://example.test/",
    sessionId: "s1",
    playerId: "p1",
    onMessage: () => {},
  });
  assert.equal(connection.urls.ws, "wss://example.test/ws/sessions/s1");
});

test("http(s) 以外のサーバ指定は拒否する", () => {
  assert.throws(
    () => new BettingConnection({ server: "ftp://example.test", sessionId: "s1", playerId: "p1", onMessage: () => {} }),
    /http\(s\)/
  );
});

test("betting.state / betting.advanced 以外の WS 封筒は無視する", () => {
  const seen = [];
  const connection = connect((kind, payload) => seen.push([kind, payload]));
  connection.receive(JSON.stringify({ type: "setup.state", payload: {} }));
  connection.receive(JSON.stringify({ type: "betting.state", payload: null }));
  connection.receive("{壊れたJSON");
  assert.deepEqual(seen, []);

  connection.receive(JSON.stringify({ type: "betting.state", payload: { phase: "betting" } }));
  connection.receive(JSON.stringify({ type: "betting.advanced", payload: { phase: "card-seed" } }));
  assert.deepEqual(seen, [
    ["betting.state", { phase: "betting" }],
    ["betting.advanced", { phase: "card-seed" }],
  ]);
});

test("切断中は送信せず、再接続中の案内を出す", async () => {
  const seen = [];
  const connection = connect((kind, payload) => seen.push([kind, payload]));
  globalThis.fetch = () => assert.fail("切断中に送信してはいけない");
  assert.equal(await connection.sendPick({ ticketId: "t" }), false);
  assert.deepEqual(seen, [["error", { message: OFFLINE }]]);
});

test("pick は playerId を添えて送り、応答の状態を流す", async () => {
  const seen = [];
  const connection = connect((kind, payload) => seen.push([kind, payload]));
  connection.online = true;
  let request = null;
  globalThis.fetch = async (url, options) => {
    request = { url, options };
    return response(200, { phase: "betting" });
  };

  const sent = await connection.sendPick({ ticketKind: "mascot", ticketId: "mascot-bear", face: "risky" });
  assert.equal(sent, true);
  assert.equal(request.url, connection.urls.picks);
  assert.equal(request.options.method, "POST");
  assert.deepEqual(JSON.parse(request.options.body), {
    playerId: "p1",
    ticketKind: "mascot",
    ticketId: "mascot-bear",
    face: "risky",
  });
  assert.deepEqual(seen, [["betting.state", { phase: "betting" }]]);
});

test("double は PUT で送る", async () => {
  const connection = connect();
  connection.online = true;
  let method = "";
  globalThis.fetch = async (url, options) => {
    method = options.method;
    return response(200, null);
  };
  await connection.sendDouble({ ticketInstanceId: "t-2" });
  assert.equal(method, "PUT");
});

test("HTTP エラーを設計どおりの文言にする", async () => {
  const cases = [
    { status: 403, send: "sendPick", message: "あなたの番ではありません" },
    { status: 409, send: "sendPick", message: "この札は残りがありません" },
    { status: 409, send: "sendDouble", message: "このレースでは使えません" },
    { status: 400, send: "sendPick", message: "セーフかリスキーを選んでください" },
    { status: 404, send: "sendPick", message: "セッションが見つかりません" },
    { status: 500, send: "sendPick", message: "通信に失敗しました。もう一度お試しください。" },
  ];
  for (const item of cases) {
    const seen = [];
    const connection = connect((kind, payload) => seen.push([kind, payload]));
    connection.online = true;
    globalThis.fetch = async () => response(item.status, {});
    assert.equal(await connection[item.send]({}), false);
    assert.deepEqual(seen, [["error", { message: item.message }]], `${item.send} ${item.status}`);
  }
});

test("サーバが文言を返したらそれを優先する", async () => {
  const seen = [];
  const connection = connect((kind, payload) => seen.push([kind, payload]));
  connection.online = true;
  globalThis.fetch = async () => response(409, { message: "この操作はできません" });
  await connection.sendPick({});
  assert.deepEqual(seen, [["error", { message: "この操作はできません" }]]);
});

test("通信自体が失敗したら再接続案内にする", async () => {
  const seen = [];
  const connection = connect((kind, payload) => seen.push([kind, payload]));
  connection.online = true;
  globalThis.fetch = async () => {
    throw new TypeError("network");
  };
  await connection.sendPick({});
  assert.deepEqual(seen, [["error", { message: OFFLINE }]]);
});

test("停止後は再接続タイマーを張らない", () => {
  const seen = [];
  const connection = connect((kind) => seen.push(kind));
  connection.close();
  connection.dropped();
  assert.deepEqual(seen, []);
  assert.equal(connection.ws, null);
});
