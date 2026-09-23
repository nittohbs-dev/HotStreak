/* ブラウザ無しで描画コードを動かすための最小 DOM スタブ。テスト専用。 */
const IDS = [
  "turn-status",
  "turn-detail",
  "race-meta",
  "ticket-list",
  "held-tickets",
  "double-picker",
  "double-slots",
  "confirm-button",
  "notice",
  "demo-bar",
  "demo-scene",
  "demo-next",
  "name-input",
  "player-count",
  "player-list",
  "foot-hint",
  "seed-meta",
  "seed-progress",
  "hand-list",
  "seeded-slot",
  "status-list",
  "side-prompt",
  "mascot-rank",
  "my-bets",
  "my-balance",
  "my-rank",
  "sheet-button",
  "all-players-sheet",
  "sheet-list",
  "sheet-close",
  "payout-title",
  "standing-list",
  "my-total",
  "breakdown-list",
  "balance-list",
];

class FakeNode {
  constructor(tag) {
    this.tag = tag;
    this.className = "";
    this.textContent = "";
    this.dataset = {};
    this.children = [];
    this.listeners = {};
    this.hidden = false;
    this.disabled = false;
    this.value = "";
    this.style = {};
  }

  findByTag(tag) {
    if (this.tag === tag) return this;
    for (const child of this.children) {
      const hit = child.findByTag(tag);
      if (hit) return hit;
    }
    return null;
  }

  type(text) {
    this.value = text;
    for (const handler of this.listeners.input || []) handler({ target: this });
  }

  append(...nodes) {
    this.children.push(...nodes);
  }

  replaceChildren(...nodes) {
    this.children = nodes;
  }

  addEventListener(type, handler) {
    (this.listeners[type] = this.listeners[type] || []).push(handler);
  }

  click() {
    for (const handler of this.listeners.click || []) handler({ stopPropagation() {} });
  }

  get text() {
    return [this.textContent, ...this.children.map((child) => child.text)].join(" ").trim();
  }

  findByClass(name) {
    if (this.className.split(" ").includes(name)) return this;
    for (const child of this.children) {
      const hit = child.findByClass(name);
      if (hit) return hit;
    }
    return null;
  }
}

function install() {
  const registry = {};
  for (const id of IDS) registry[id] = new FakeNode("div");
  globalThis.document = {
    createElement: (tag) => new FakeNode(tag),
    getElementById: (id) => registry[id],
  };
  return registry;
}

module.exports = { FakeNode, install, IDS };
