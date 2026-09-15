/* API-BETTING-001〜003 と WS 購読。ブラウザ専用。封筒の形は README の接続契約を参照。 */
(function (root, factory) {
  const api = factory();
  if (typeof module === "object" && module.exports) module.exports = api;
  else root.HotStreakBettingConnection = api;
})(typeof globalThis !== "undefined" ? globalThis : this, function () {
  const RETRY_MS = 1000;
  const OFFLINE = "接続が切れました。再接続しています…";

  const COMMON_ERRORS = {
    400: "セーフかリスキーを選んでください",
    403: "あなたの番ではありません",
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
      state: `${base}/api/sessions/${session}/betting`,
      picks: `${base}/api/sessions/${session}/betting/picks`,
      double: `${base}/api/sessions/${session}/betting/double`,
      ws: `${base.replace(/^http/, "ws")}/ws/sessions/${session}`,
    };
  }

  class BettingConnection {
    constructor(options) {
      this.urls = endpoints(options.server, options.sessionId);
      this.playerId = options.playerId;
      this.onMessage = options.onMessage;
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

    /* 購読を先に確立し、スナップショットとの間のイベントを取りこぼさない。 */
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
      ws.onopen = () => this.loadSnapshot();
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

    async loadSnapshot() {
      try {
        const response = await fetch(this.urls.state, { headers: { Accept: "application/json" } });
        if (!response.ok) throw response;
        const snapshot = await response.json();
        this.online = true;
        this.onMessage("betting.state", snapshot);
      } catch (failure) {
        this.onMessage("error", { message: await this.describe(failure, {}) });
        if (this.ws) this.ws.close();
      }
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
      if ((kind === "betting.state" || kind === "betting.advanced") && payload && typeof payload === "object") {
        this.onMessage(kind, payload);
      }
    }

    sendPick(body) {
      return this.send("POST", this.urls.picks, body, { 409: "この札は残りがありません" });
    }

    sendDouble(body) {
      return this.send("PUT", this.urls.double, body, { 409: "このレースでは使えません" });
    }

    async send(method, url, body, extraErrors) {
      if (!this.online) {
        this.onMessage("error", { message: OFFLINE });
        return false;
      }
      try {
        const response = await fetch(url, {
          method,
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(Object.assign({ playerId: this.playerId }, body)),
        });
        if (!response.ok) throw response;
        // HTTP 応答もサーバの確定結果。WS の重複通知は画面側が無視する。
        const result = await response.json().catch(() => null);
        if (result && typeof result === "object") this.onMessage("betting.state", result);
        return true;
      } catch (failure) {
        this.onMessage("error", { message: await this.describe(failure, extraErrors) });
        return false;
      }
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

  return { BettingConnection, OFFLINE };
});
