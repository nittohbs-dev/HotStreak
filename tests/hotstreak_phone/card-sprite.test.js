/* atlas の切り出し計算。ブラウザで絵が出るかまでは保証しないが、位置の計算を固定する。 */
const test = require("node:test");
const assert = require("node:assert/strict");

const fakeDom = require("./fake-dom.js");
const { cropStyle, ATLAS } = require("../../src/hotstreak_phone/card-sprite.js");

test("先頭のカードは枠だけ縮めてずらさない", () => {
  assert.deepEqual(cropStyle([0, 0, 240, 336], 0.5), {
    width: 120,
    height: 168,
    left: -0,
    top: -0,
    scale: 0.5,
  });
});

test("atlas 内の位置に応じて中の画像をずらす", () => {
  const crop = cropStyle([720, 672, 240, 336], 0.5);
  assert.equal(crop.width, 120);
  assert.equal(crop.height, 168);
  assert.equal(crop.left, -360, "x を倍率どおりに左へずらす");
  assert.equal(crop.top, -336, "y を倍率どおりに上へずらす");
});

test("等倍ならカード1枚分の大きさになる", () => {
  const crop = cropStyle([1440, 2352, 240, 336], 1);
  assert.equal(crop.width, 240);
  assert.equal(crop.height, 336);
  assert.equal(crop.left, -1440);
  assert.equal(crop.top, -2352);
});

test("枠と画像に計算どおりの style を与える", () => {
  fakeDom.install();
  delete require.cache[require.resolve("../../src/hotstreak_phone/card-sprite.js")];
  const { cardArt } = require("../../src/hotstreak_phone/card-sprite.js");

  const box = cardArt([720, 1680, 240, 336], 0.42);
  assert.equal(box.className, "card-art");
  assert.equal(box.style.width, "100.8px");
  assert.equal(box.style.height, "141.12px");

  const sheet = box.children[0];
  assert.equal(sheet.tag, "img");
  assert.equal(sheet.src, ATLAS);
  assert.equal(sheet.alt, "", "装飾なので読み上げ対象にしない");
  assert.equal(sheet.style.left, "-302.4px");
  assert.equal(sheet.style.top, "-705.6px");
  assert.equal(sheet.style.transform, "scale(0.42)");
});

test("素材が読めなければ画像を隠す（ラベルで補う）", () => {
  fakeDom.install();
  delete require.cache[require.resolve("../../src/hotstreak_phone/card-sprite.js")];
  const { cardArt } = require("../../src/hotstreak_phone/card-sprite.js");

  const sheet = cardArt([0, 0, 240, 336], 0.42).children[0];
  assert.equal(sheet.hidden, false);
  for (const handler of sheet.listeners.error || []) handler({});
  assert.equal(sheet.hidden, true);
});
