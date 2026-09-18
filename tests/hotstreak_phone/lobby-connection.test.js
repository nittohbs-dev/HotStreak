/* API-LOBBY-003/004 のパス組み立てとエラー文言を検証する。 */
const test = require("node:test");
const assert = require("node:assert/strict");

const { LobbyConnection, OFFLINE } = require("../../src/hotstreak_phone/lobby-connection.js");

function connect(onMessage) {
  return new LobbyConnection({
    server: "http://127.0.0.1:8000",
    sessionId: "S 1",
    onMessage: onMessage || (() => {}),
  });
}

function response(status, body) {
  return { ok: status < 400, status, json: async () => body };
}

test("エンドポイントを設計どおりに組み立て、sessionId をエスケープする", () => {
  const connection = connect();
  assert.equal(connection.urls.base, "http://127.0.0.1:8000/api/sessions/S%201");
  assert.equal(connection.urls.join, "http://127.0.0.1:8000/api/sessions/S%201/join");
  assert.equal(connection.urls.ws, "ws://127.0.0.1:8000/ws/sessions/S%201");
});

test("http(s) 以外のサーバ指定は拒否する", () => {
  assert.throws(() => new LobbyConnection({ server: "ftp://x.test", sessionId: "s1", onMessage: () => {} }), /http\(s\)/);
});

test("購読後に join し、playerId を保持する", async () => {
  const seen = [];
  const connection = connect((kind, payload) => seen.push([kind, payload]));
  const calls = [];
  globalThis.fetch = async (url, options) => {
    calls.push([options.method, url]);
    return response(200, { playerId: "p_9", phase: "lobby", players: [] });
  };

  await connection.enterLobby();
  assert.deepEqual(calls, [["POST", connection.urls.join]]);
  assert.equal(seen[0][0], "joined");
  assert.equal(connection.playerId, "p_9");
  assert.equal(connection.online, true);
});

test("再接続後は join し直さず状態を取り直す", async () => {
  const seen = [];
  const connection = connect((kind) => seen.push(kind));
  connection.playerId = "p_9";
  const calls = [];
  globalThis.fetch = async (url, options) => {
    calls.push([options.method, url]);
    return response(200, { phase: "lobby", players: [] });
  };

  await connection.enterLobby();
  assert.deepEqual(calls, [["GET", connection.urls.base]]);
  assert.deepEqual(seen, ["lobby.state"]);
});

test("名前確定は playerId 入りのパスへ PUT する", async () => {
  const seen = [];
  const connection = connect((kind, payload) => seen.push([kind, payload]));
  connection.playerId = "p 9";
  connection.online = true;
  let request = null;
  globalThis.fetch = async (url, options) => {
    request = { url, options };
    return response(200, { phase: "lobby", players: [{ playerId: "p 9", displayName: "ヤマダ", nameReady: true }] });
  };

  assert.equal(await connection.sendName({ displayName: "ヤマダ" }), true);
  assert.equal(request.url, "http://127.0.0.1:8000/api/sessions/S%201/players/p%209/name");
  assert.equal(request.options.method, "PUT");
  assert.deepEqual(JSON.parse(request.options.body), { displayName: "ヤマダ" });
  assert.equal(seen[0][0], "lobby.state");
});

test("切断中は送信せず、再接続中の案内を出す", async () => {
  const seen = [];
  const connection = connect((kind, payload) => seen.push([kind, payload]));
  connection.playerId = "p_9";
  globalThis.fetch = () => assert.fail("切断中に送信してはいけない");
  assert.equal(await connection.sendName({ displayName: "ヤマダ" }), false);
  assert.deepEqual(seen, [["error", { message: OFFLINE }]]);
});

test("join 前の名前確定は送信しない", async () => {
  const seen = [];
  const connection = connect((kind, payload) => seen.push([kind, payload]));
  connection.online = true;
  globalThis.fetch = () => assert.fail("playerId 未取得で送信してはいけない");
  assert.equal(await connection.sendName({ displayName: "ヤマダ" }), false);
  assert.deepEqual(seen, [["error", { message: OFFLINE }]]);
});

test("HTTP エラーを設計どおりの文言にする", async () => {
  const cases = [
    { status: 400, message: "名前を入力してください" },
    { status: 403, message: "操作できません" },
    { status: 404, message: "セッションが見つかりません" },
    { status: 500, message: "通信に失敗しました。もう一度お試しください。" },
  ];
  for (const item of cases) {
    const seen = [];
    const connection = connect((kind, payload) => seen.push([kind, payload]));
    connection.playerId = "p_9";
    connection.online = true;
    globalThis.fetch = async () => response(item.status, {});
    assert.equal(await connection.sendName({ displayName: "ヤマダ" }), false);
    assert.deepEqual(seen, [["error", { message: item.message }]], String(item.status));
  }
});

test("満員・受付終了の join は案内を出して再接続へ回す", async () => {
  const seen = [];
  const connection = connect((kind, payload) => seen.push([kind, payload]));
  globalThis.fetch = async () => response(409, {});
  await connection.enterLobby();
  assert.deepEqual(seen, [["error", { message: "参加できません（満員または受付は終了しました）" }]]);

  const withMessage = [];
  const other = connect((kind, payload) => withMessage.push([kind, payload]));
  globalThis.fetch = async () => response(409, { message: "受付は終了しました" });
  await other.enterLobby();
  assert.deepEqual(withMessage, [["error", { message: "受付は終了しました" }]]);
});

test("購読する封筒は lobby と setup の進行だけ", () => {
  const seen = [];
  const connection = connect((kind, payload) => seen.push([kind, payload]));
  connection.receive(JSON.stringify({ type: "betting.state", payload: {} }));
  connection.receive(JSON.stringify({ type: "lobby.state", payload: null }));
  connection.receive("{壊れたJSON");
  assert.deepEqual(seen, []);

  connection.receive(JSON.stringify({ type: "lobby.state", payload: { phase: "lobby" } }));
  connection.receive(JSON.stringify({ type: "lobby.advanced", payload: { phase: "setup-cards" } }));
  connection.receive(JSON.stringify({ type: "setup.advanced", payload: { phase: "betting" } }));
  assert.deepEqual(seen.map((entry) => entry[0]), ["lobby.state", "lobby.advanced", "setup.advanced"]);
});

test("停止後は再接続タイマーを張らない", () => {
  const seen = [];
  const connection = connect((kind) => seen.push(kind));
  connection.close();
  connection.dropped();
  assert.deepEqual(seen, []);
  assert.equal(connection.ws, null);
});
