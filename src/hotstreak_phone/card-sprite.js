/* カード絵を atlas から切り出す。素材は Display と同じ assets/images/cards/cards_atlas.png。 */
(function (root, factory) {
  const api = factory();
  if (typeof module === "object" && module.exports) module.exports = api;
  else root.HotStreakCardSprite = api;
})(typeof globalThis !== "undefined" ? globalThis : this, function () {
  const ATLAS = "../../assets/images/cards/cards_atlas.png";

  /* atlas 全体の画素数を知らなくても、枠で切り抜いて中の画像をずらせば1枚分になる。 */
  function cropStyle(rect, scale) {
    const [x, y, width, height] = rect;
    return {
      width: width * scale,
      height: height * scale,
      left: -x * scale,
      top: -y * scale,
      scale,
    };
  }

  function px(value) {
    return `${Math.round(value * 100) / 100}px`;
  }

  function cardArt(rect, scale) {
    const crop = cropStyle(rect, scale);
    const box = document.createElement("div");
    box.className = "card-art";
    box.style.width = px(crop.width);
    box.style.height = px(crop.height);

    const sheet = document.createElement("img");
    sheet.className = "card-art-sheet";
    sheet.src = ATLAS;
    sheet.alt = "";
    sheet.style.left = px(crop.left);
    sheet.style.top = px(crop.top);
    sheet.style.transform = `scale(${crop.scale})`;
    // 素材が読めない環境でも、隣に出すラベルで内容が分かるようにする。
    sheet.addEventListener("error", () => {
      sheet.hidden = true;
    });

    box.append(sheet);
    return box;
  }

  return { cropStyle, cardArt, ATLAS };
});
