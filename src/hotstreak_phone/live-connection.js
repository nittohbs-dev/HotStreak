/* 同一会場サーバのREST/WS。進行と金額の正本は常にサーバ。 */
(function (root, factory) {
  const api = factory();
  if (typeof module === "object" && module.exports) module.exports = api;
  else root.HotStreakLive = api;
})(typeof globalThis !== "undefined" ? globalThis : this, function () {
  const PAGES = { lobby: "lobby", "setup-cards": "lobby", betting: "betting", "card-seed": "card-seed", race: "race", payout: "payout" };
  const EVENTS = { lobby: "lobby.state", "setup-cards": "lobby.advanced", betting: "betting.state", "card-seed": "seed.state", race: "race.state", payout: "payout.state" };
  const OFFLINE = "接続が切れました。再接続しています…";

  class Connection {
    constructor(options) {
      this.phase = options.phase;
      this.sessionId = options.sessionId;
      this.playerId = options.playerId || null;
      this.onMessage = options.onMessage;
      const url = new URL(options.server || location.origin);
      if (!["http:", "https:"].includes(url.protocol)) throw new Error("server は http(s)://host[:port] 形式で指定してください");
      this.server = url.origin;
      this.base = `${this.server}/api/sessions/${encodeURIComponent(this.sessionId)}`;
      this.closed = false;
      this.online = false;
      this.loading = false;
      this.again = false;
      this.revision = -1;
      this.ws = null;
      this.retry = null;
      this.pendingAction = null;
    }

    async request(path, method = "GET", body, key) {
      const headers = { Accept: "application/json" };
      if (body !== undefined) headers["Content-Type"] = "application/json";
      if (key) headers["Idempotency-Key"] = key;
      const response = await fetch(this.base + path, {
        method, credentials: "same-origin", headers,
        ...(body !== undefined ? { body: JSON.stringify(body) } : {}),
      });
      const data = await response.json().catch(() => ({}));
      if (!response.ok) {
        const error = new Error(data.message || "操作に失敗しました。もう一度お試しください。");
        error.status = response.status;
        throw error;
      }
      return data;
    }

    async start() {
      try {
        if (this.phase === "lobby" && !this.playerId) {
          const joined = await this.request("/join", "POST", {});
          this.playerId = joined.playerId;
          this.onMessage("joined", joined);
        }
        if (!this.closed) this.connect();
      } catch (error) {
        this.onMessage("error", { message: error.message });
      }
    }

    connect() {
      if (this.closed || this.ws) return;
      const ws = new WebSocket(`${this.server.replace(/^http/, "ws")}/ws/sessions/${encodeURIComponent(this.sessionId)}`);
      this.ws = ws;
      ws.onopen = () => { this.online = true; this.refresh(); };
      // 手札はWSで配らない。認証付きGETで本人のスナップショットを取り直す。
      ws.onmessage = () => this.refresh();
      ws.onerror = () => ws.close();
      ws.onclose = () => {
        this.ws = null;
        this.online = false;
        if (this.closed) return;
        this.onMessage("disconnected", {});
        this.retry = setTimeout(() => this.connect(), 1000);
      };
    }

    async refresh() {
      if (this.closed) return;
      if (this.loading) { this.again = true; return; }
      this.loading = true;
      try {
        do {
          this.again = false;
          const snapshot = await this.request("");
          if (this.closed || snapshot.revision < this.revision) continue;
          this.revision = snapshot.revision;
          const page = PAGES[snapshot.phase];
          if (!page) throw new Error("ゲームの状態を確認できません");
          if (page !== PAGES[this.phase]) {
            const query = new URLSearchParams({ session: this.sessionId });
            const pid = snapshot.playerId || this.playerId;
            if (snapshot.phase !== "lobby" && pid) query.set("player", pid);
            if (this.server !== location.origin) query.set("server", this.server);
            this.close();
            location.assign(`${page}.html?${query}`);
            return;
          }
          if (!snapshot.playerId && this.phase !== "lobby") {
            throw new Error("参加情報を確認できません。会場のQRから参加し直してください。");
          }
          if (this.phase === "lobby" && snapshot.phase === "lobby") {
            this.onMessage("joined", { ...snapshot, playerId: this.playerId });
          } else {
            this.onMessage(EVENTS[snapshot.phase], snapshot);
          }
        } while (this.again && !this.closed);
      } catch (error) {
        if (!this.closed) this.onMessage("error", { message: error.status ? error.message : OFFLINE });
      } finally {
        this.loading = false;
      }
    }

    async send(path, method, body) {
      if (!this.online || this.closed) {
        this.onMessage("error", { message: OFFLINE });
        return false;
      }
      const signature = JSON.stringify([path, method, body]);
      if (!this.pendingAction || this.pendingAction.signature !== signature) {
        const key = Array.from(crypto.getRandomValues(new Uint8Array(16)), n => n.toString(16).padStart(2, "0")).join("");
        this.pendingAction = { signature, key };
      }
      try {
        await this.request(path, method, body, this.pendingAction.key);
        this.pendingAction = null;
        await this.refresh();
        return true;
      } catch (error) {
        // 通信結果不明の再送は同じ操作IDを使い、連続手番でも二重取得しない。
        if (error.status) this.pendingAction = null;
        this.onMessage("error", { message: error.status ? error.message : OFFLINE });
        return false;
      }
    }

    sendName(body) { return this.send(`/players/${encodeURIComponent(this.playerId)}/name`, "PUT", body); }
    sendPick(body) { return this.send("/betting/picks", "POST", body); }
    sendDouble(body) { return this.send("/betting/double", "PUT", body); }
    sendSeed(body) { return this.send("/seed", "POST", body); }

    close() {
      this.closed = true;
      clearTimeout(this.retry);
      if (this.ws) this.ws.close();
      this.ws = null;
    }
  }
  return { Connection, PAGES, EVENTS };
});
