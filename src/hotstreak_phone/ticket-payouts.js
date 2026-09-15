/* payout README の観測確定額表（OPEN-payout-002）。表示専用で精算はしない。 */
(function (root, factory) {
  const api = factory();
  if (typeof module === "object" && module.exports) module.exports = api;
  else root.HotStreakTicketPayouts = api;
})(typeof globalThis !== "undefined" ? globalThis : this, function () {
  const MASCOT = {
    safe: { top: [10, 7, 5], mid: [7, 5, 3], bot: [5, 3, 2] },
    risky: { top: [15, 5, 2], mid: [11, 3, 1], bot: [8, 2, 0] },
  };
  const SIDE = {
    safe: { top: [10, 0], mid: [7, 0], bot: [5, 0] },
    risky: { top: [15, -5], mid: [12, -5], bot: [10, -5] },
  };

  function money(amount) {
    return amount < 0 ? `-$${Math.abs(amount)}` : `$${amount}`;
  }

  function amounts(kind, face, tier) {
    const table = kind === "side" ? SIDE : MASCOT;
    const row = table[face];
    return row && row[tier] ? row[tier] : null;
  }

  function summary(kind, face, tier) {
    const values = amounts(kind, face, tier);
    if (!values) return "";
    if (kind === "side") {
      return `正解 ${money(values[0])}・外れ ${money(values[1])}`;
    }
    return `1着 ${money(values[0])}・2着 ${money(values[1])}・3着 ${money(values[2])}（4着 $0）`;
  }

  return { amounts, summary, money };
});
