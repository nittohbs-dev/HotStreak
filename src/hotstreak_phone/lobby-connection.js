/* API-LOBBY-003/004 と WS 購読。ブラウザ専用。封筒の形は README の接続契約を参照。 */
(function (root, factory) {
  const api = factory();
  if (typeof module === "object" && module.exports) module.exports = api;
  else root.HotStreakLobbyConnection = api;
})(typeof globalThis !== "undefined" ? globalThis : this, function () {
  const RETRY_MS = 1000;
  const OFFLINE = "接続が切れました。再接続しています…";
  const EVENTS = ["lobby.state", "lobby.advanced", "setup.advanced"];

  const COMMON_ERRORS = {
    400: "名前を入力してください",
    403: "操作できません",
    404: "セッションが見つかりません",
  };

  function endpoints(server, sessionId) {
    const url = new URL(server);
    if (url.protocol !== "http:" && url.protocol !== "https:") {
      throw new Error("server は http(s)://host[:port] 形式で指定してください");
    }
    const base = `${url.origin}${url.pathname.replace(/\/$/, "")}`;
    const session = encodeURIComponent(sessionId);
    return {
      base: `${base}/api/sessions/${session}`,
      join: `${base}/api/sessions/${session}/join`,
      ws: `${base.replace(/^http/, "ws")}/ws/sessions/${session}`,
    };
  }

  class LobbyConnection {
    constructor(options) {
      this.urls = endpoints(options.server, options.sessionId);
      this.onMessage = options.onMessage;
      this.playerId = null;
      this.ws = null;
      this.stopped = false;
      this.online = false;
      this.retry = null;
    }

    start() {
      this.stopped = false;
      this.connect();
    }

    close() {
      this.stopped = true;
      this.online = false;
      clearTimeout(this.retry);
      if (this.ws) this.ws.close();
      this.ws = null;
    }

    /* 購読を先に確立し、join 応答との間のイベントを取りこぼさない。 */
    connect() {
      if (this.stopped || this.ws) return;
      let ws;
      try {
        ws = new WebSocket(this.urls.ws);
      } catch (error) {
        this.dropped();
        return;
      }
      this.ws = ws;
      ws.onopen = () => this.enterLobby();
      ws.onmessage = (event) => this.receive(event.data);
      ws.onerror = () => ws.close();
      ws.onclose = () => this.dropped();
    }

    dropped() {
      if (this.ws) {
        this.ws.onopen = this.ws.onmessage = this.ws.onerror = this.ws.onclose = null;
      }
      this.ws = null;
      if (this.stopped) return;
      this.online = false;
      this.onMessage("disconnected", {});
      clearTimeout(this.retry);
      this.retry = setTimeout(() => this.connect(), RETRY_MS);
    }

    /* 初回は join、再接続後は状態の取り直しだけ行う（再参加はスコープ外）。 */
    async enterLobby() {
      try {
        const snapshot = this.playerId ? await this.request("GET", this.urls.base) : await this.join();
        this.online = true;
        this.onMessage(this.playerId ? "lobby.state" : "joined", snapshot);
        if (!this.playerId && snapshot && typeof snapshot.playerId === "string") {
          this.playerId = snapshot.playerId;
        }
      } catch (failure) {
        this.onMessage("error", { message: await this.describe(failure, { 409: "参加できません（満員または受付は終了しました）" }) });
        if (this.ws) this.ws.close();
      }
    }

    join() {
      return this.request("POST", this.urls.join, {});
    }

    sendName(body) {
      if (!this.playerId) {
        this.onMessage("error", { message: OFFLINE });
        return Promise.resolve(false);
      }
      const url = `${this.urls.base}/players/${encodeURIComponent(this.playerId)}/name`;
      return this.send("PUT", url, body);
    }

    receive(raw) {
      let event;
      try {
        event = JSON.parse(raw);
      } catch (error) {
        return;
      }
      const kind = event && event.type;
      const payload = event && event.payload;
      if (EVENTS.includes(kind) && payload && typeof payload === "object") {
        this.onMessage(kind, payload);
      }
    }

    async send(method, url, body) {
      if (!this.online) {
        this.onMessage("error", { message: OFFLINE });
        return false;
      }
      try {
        const result = await this.request(method, url, body);
        // HTTP 応答もサーバの確定結果。WS の重複通知は画面側が無視する。
        if (result && typeof result === "object" && Array.isArray(result.players)) {
          this.onMessage("lobby.state", result);
        }
        return true;
      } catch (failure) {
        this.onMessage("error", { message: await this.describe(failure, {}) });
        return false;
      }
    }

    async request(method, url, body) {
      const options = { method, headers: { Accept: "application/json" } };
      if (body !== undefined) {
        options.headers["Content-Type"] = "application/json";
        options.body = JSON.stringify(body);
      }
      const response = await fetch(url, options);
      if (!response.ok) throw response;
      return response.json().catch(() => null);
    }

    async describe(failure, extraErrors) {
      if (!failure || typeof failure.status !== "number") return OFFLINE;
      const fromServer = await failure
        .json()
        .then((body) => (body && typeof body.message === "string" ? body.message : ""))
        .catch(() => "");
      if (fromServer) return fromServer;
      return (
        extraErrors[failure.status] ||
        COMMON_ERRORS[failure.status] ||
        (failure.status === 409 ? "この操作はできません" : "通信に失敗しました。もう一度お試しください。")
      );
    }
  }

  return { LobbyConnection, OFFLINE };
});
