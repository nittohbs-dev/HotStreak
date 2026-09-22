/* hidden 属性が効くことを守る。display 指定のある要素で hidden が無視されると、
   小画面の膜が画面を覆って操作できなくなる（実際に起きた不具合の回帰防止）。 */
const test = require("node:test");
const assert = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");

const PHONE_DIR = path.join(__dirname, "../../src/hotstreak_phone");

function read(name) {
  return fs.readFileSync(path.join(PHONE_DIR, name), "utf8");
}

test("phone.css が hidden 属性を display 指定より優先させる", () => {
  const css = read("phone.css");
  assert.match(css, /\[hidden\]\s*\{[^}]*display:\s*none\s*!important/);
});

test("hidden を使う画面はすべて phone.css を読み込んでいる", () => {
  const pages = fs.readdirSync(PHONE_DIR).filter((name) => name.endsWith(".html"));
  assert.ok(pages.length >= 4, "画面が見つからない");
  for (const page of pages) {
    const html = read(page);
    if (!html.includes(" hidden")) continue;
    assert.match(html, /href="phone\.css"/, `${page} が phone.css を読み込んでいない`);
  }
});
