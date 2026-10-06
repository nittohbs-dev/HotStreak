/* 起動済みの実サーバに、Cookieが独立した3人のスマホで参加する。 */
const { chromium } = require('playwright');
const assert = require('node:assert/strict');
const { randomUUID } = require('node:crypto');
const fs = require('node:fs');
const path = require('node:path');

(async () => {
  const origin = process.env.HOTSTREAK_TEST_URL || 'http://127.0.0.1:8010';
  const browser = await chromium.launch({ headless: true, channel: 'msedge' });
  const failures = [];
  const contexts = [];
  try {
    const created = await (await fetch(origin+'/api/sessions', { method: 'POST' })).json();
    const base = origin+'/api/sessions/'+created.sessionId;
    const snapshot = async () => (await fetch(base)).json();
    async function advance() {
      const s = await snapshot();
      const response = await fetch(base+'/advance', { method: 'POST', headers: {
        'Content-Type': 'application/json', 'Idempotency-Key': randomUUID(), 'X-Display-Token': created.displayToken,
      }, body: JSON.stringify({ phase: s.phase, revision: s.revision }) });
      assert.equal(response.status, 200, await response.text());
      return snapshot();
    }
    const people = [];
    for (let i = 0; i < 3; i++) {
      const context = await browser.newContext({ viewport: { width: 390, height: 844 } });
      contexts.push(context);
      const page = await context.newPage();
      page.on('pageerror', error => failures.push(error.message));
      page.on('response', response => { if (response.status() >= 400 && !response.url().endsWith('/favicon.ico')) failures.push(`${response.status()} ${response.url()}`); });
      await page.goto(origin+created.joinUrl);
      await page.locator('#name-input').fill(`参加者${i+1}`);
      await page.locator('#confirm-button').click();
      await page.waitForFunction(() => document.querySelector('#name-input').disabled);
      const pid = await page.evaluate(sid => sessionStorage.getItem(`hotstreak-player-${sid}`), created.sessionId);
      people.push({ page, pid, context });
    }
    await advance();
    await people[0].page.waitForFunction(() => document.querySelector('#notice').textContent.includes('公開カード'));
    await advance();
    for (let race = 1; race <= 3; race++) {
      for (const { page } of people) await page.waitForURL(/betting\.html/);
      // 再読込しても同じ参加者として復帰する。
      await people[0].page.reload();
      for (let turn = 0; turn < 6; turn++) {
        const s = await snapshot();
        const { page } = people.find(p => p.pid === s.currentPlayerId);
        await page.waitForFunction(() => document.querySelector('#turn-status').dataset.mode === 'mine');
        await page.locator('#ticket-list .ticket[data-sold-out="false"]').first().click();
        await page.locator('#confirm-button').click();
        await page.waitForFunction(() => document.querySelector('#notice').dataset.error !== 'true');
        // WSによる全員への更新を待ってから、次の手番を取得する。
        for (let retry = 0; retry < 100; retry++) {
          if ((await snapshot()).turnIndex === turn+1) break;
          await new Promise(resolve => setTimeout(resolve, 20));
        }
        assert.equal((await snapshot()).turnIndex, turn+1);
      }
      if (race === 3) {
        for (const { page } of people) {
          await page.locator('#double-slots button').first().click();
        }
        for (let retry = 0; retry < 100; retry++) {
          if (Object.values((await snapshot()).doubleByPlayer).every(Boolean)) break;
          await new Promise(resolve => setTimeout(resolve, 20));
        }
      }
      await advance();
      for (const { page } of people) {
        await page.waitForURL(/card-seed\.html/);
        await page.locator('#hand-list .hand-card').first().click();
        await page.locator('#confirm-button').click();
        await page.locator('#seeded-slot').waitFor({ state: 'visible' });
        assert.equal(await page.locator('#hand-list .hand-card').count(), 2);
      }
      await advance();
      for (const { page } of people) await page.waitForURL(/race\.html/);
      let state;
      for (let count = 0; count < 61; count++) {
        state = await advance();
        if (state.phase === 'payout') break;
      }
      assert.equal(state.phase, 'payout');
      for (const { page } of people) {
        await page.waitForURL(/payout\.html/);
        await page.waitForFunction(() => document.querySelector('#notice').dataset.error !== 'true');
        assert(!((await page.locator('body').innerText()).includes('情報を確認できません')));
      }
      if (process.env.HOTSTREAK_ARTIFACTS) {
        fs.mkdirSync(process.env.HOTSTREAK_ARTIFACTS, { recursive: true });
        await people[0].page.screenshot({ path: path.join(process.env.HOTSTREAK_ARTIFACTS, `payout-race-${race}.png`), fullPage: true });
      }
      await advance();
    }
    for (const { page } of people) await page.waitForURL(/lobby\.html/);
    assert.deepEqual(failures, []);
    console.log('PASS: 独立した3ブラウザで参加・3レース・配当・再参加まで完了');
  } finally {
    await Promise.all(contexts.map(c => c.close()));
    await browser.close();
  }
})().catch(error => { console.error(error); process.exitCode = 1; });
