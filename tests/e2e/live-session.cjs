/* 起動済みの実サーバに、Cookieが独立した3人のスマホで参加する。 */
const { chromium } = require(process.env.HOTSTREAK_PLAYWRIGHT_MODULE || 'playwright');
const assert = require('node:assert/strict');
const { randomUUID } = require('node:crypto');
const fs = require('node:fs');
const path = require('node:path');

(async () => {
  const origin = process.env.HOTSTREAK_TEST_URL || 'http://127.0.0.1:8010';
  const browser = await chromium.launch({ headless: true, channel: process.env.HOTSTREAK_BROWSER_CHANNEL || 'msedge' });
  const failures = [];
  const contexts = [];
  let enterDisplay, displayExit;
  try {
    if (process.env.HOTSTREAK_ARTIFACTS) fs.mkdirSync(process.env.HOTSTREAK_ARTIFACTS, { recursive: true });
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
    if (process.env.HOTSTREAK_PHONE_ENTER === '1') {
      const { spawn } = require('node:child_process');
      enterDisplay = spawn('uv', ['run', '--python', '3.12', '--with-requirements', 'requirements.txt',
        'python', 'tests/e2e/phone-enter-display.py'], { env: { ...process.env, PYTHONPATH: 'src' } });
      let output = '';
      enterDisplay.stdout.on('data', data => { output += data; });
      enterDisplay.stderr.on('data', data => { output += data; });
      displayExit = new Promise(resolve => enterDisplay.on('close', code => resolve({ code, output })));
      enterDisplay.stdin.end(JSON.stringify({ origin, credentials: created }));
    }
    const people = [];
    for (let i = 0; i < 3; i++) {
      const context = await browser.newContext({ viewport: { width: 390, height: 844 } });
      if (process.env.HOTSTREAK_DROP_WS === '1') {
        // 接続自体はOPENのまま、通知だけ届かないスマホを再現する。
        await context.addInitScript(() => {
          const NativeWebSocket = window.WebSocket;
          window.WebSocket = class extends NativeWebSocket {
            constructor(...args) {
              super(...args);
              this.addEventListener('message', event => event.stopImmediatePropagation());
            }
          };
        });
      }
      contexts.push(context);
      const page = await context.newPage();
      page.on('pageerror', error => failures.push(error.message));
      page.on('response', response => { if (response.status() >= 400 && !response.url().endsWith('/favicon.ico')) failures.push(`${response.status()} ${response.url()}`); });
      await page.goto(new URL(created.joinUrl, process.env.HOTSTREAK_PHONE_ORIGIN || origin).href);
      await page.locator('#name-input').fill(`参加者${i+1}`);
      await page.locator('#confirm-button').click();
      await page.waitForFunction(() => document.querySelector('#name-input').disabled);
      const personal = await (await page.request.get(new URL(new URL(base).pathname, page.url()).href)).json();
      const pid = personal.viewerPlayerId || personal.playerId;
      assert(pid, '本人のプレイヤーIDを取得できる');
      people.push({ page, pid, context });
    }
    async function phoneAdvance() {
      const before = await snapshot();
      await people[0].page.waitForFunction(() => {
        const button = document.getElementById('host-advance');
        return button && !button.disabled && !document.getElementById('host-controls').hidden;
      });
      await people[0].page.locator('#host-advance').click();
      for (let i = 0; i < 100; i++) {
        if ((await snapshot()).phase !== before.phase) return;
        await new Promise(resolve => setTimeout(resolve, 30));
      }
      throw new Error('Phoneの進行が反映されません');
    }
    for (const { page } of people.slice(1)) assert(await page.locator('#host-controls').isHidden());
    await phoneAdvance();
    await people[0].page.waitForFunction(() => document.querySelector('#notice').textContent.includes('公開カード'));
    await phoneAdvance();
    for (let race = 1; race <= 3; race++) {
      for (const { page } of people) await page.waitForURL(/betting\.html/);
      assert.equal((await people[0].page.request.get(base)).ok(), true);
      assert.equal((await (await people[0].page.request.get(base)).json()).hostPlayerId, people[0].pid);
      assert.equal(await people[0].page.locator('#host-advance').innerText(), 'ENTER');
      for (const { page } of people.slice(1)) assert(await page.locator('#host-controls').isHidden());
      // 再読込しても同じ参加者として復帰する。
      if (process.env.HOTSTREAK_DROP_WS !== '1') await people[0].page.reload();
      for (let turn = 0; turn < 6; turn++) {
        const s = await snapshot();
        const { page } = people.find(p => p.pid === s.currentPlayerId);
        await page.waitForFunction(() => document.querySelector('#turn-status').dataset.mode === 'mine');
        await page.locator('#ticket-list .ticket[data-sold-out="false"]').first().click();
        await page.locator('#confirm-button').click();
        await page.waitForFunction(() => document.querySelector('#notice').dataset.error !== 'true');
        // WSによる全員への更新を待ってから、次の手番を取得する。
        for (let retry = 0; retry < 100; retry++) {
          if (Object.values((await snapshot()).picksByPlayer).flat().length === turn+1) break;
          await new Promise(resolve => setTimeout(resolve, 20));
        }
        assert.equal(Object.values((await snapshot()).picksByPlayer).flat().length, turn+1);
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
      await phoneAdvance();
      for (const { page } of people) {
        await page.waitForURL(/card-seed\.html/);
        await page.locator('#hand-list .hand-card').first().click();
        await page.locator('#confirm-button').click();
        await page.locator('#seeded-slot').waitFor({ state: 'visible' });
        assert.equal(await page.locator('#hand-list .hand-card').count(), 2);
      }
      await phoneAdvance();
      for (const { page } of people) await page.waitForURL(/race\.html/);
      let state;
      if (process.env.HOTSTREAK_PHONE_ENTER === '1') {
        const page = people[0].page;
        const waitState = async predicate => {
          for (let i = 0; i < 500; i++) {
            const value = await snapshot();
            if (predicate(value)) return value;
            await new Promise(resolve => setTimeout(resolve, 50));
          }
          throw new Error('Phone ENTERの状態待ちがタイムアウトしました');
        };
        const button = page.locator('#host-advance');
        await waitState(s => s.enterControl?.canTap);
        for (const { page: other } of people.slice(1)) assert(await other.locator('#host-controls').isHidden());
        assert.equal(await button.innerText(), 'ENTER');
        if (race === 1) {
          // 指のキャンセルでは長押しが残らない。
          const cancelBox = await button.boundingBox();
          await page.mouse.move(cancelBox.x + cancelBox.width/2, cancelBox.y + cancelBox.height/2);
          await page.mouse.down();
          await button.dispatchEvent('pointercancel', { pointerId: 1 });
          await page.mouse.up();
          await page.waitForTimeout(1100);
          assert.equal((await snapshot()).revealed, 0);
        }
        await button.click();
        await waitState(s => s.revealed === 1 && s.enterControl?.canTap);
        assert.equal((await snapshot()).enterControl.autoRunning, false);
        const hold = async () => {
          const box = await button.boundingBox();
          await page.mouse.move(box.x + box.width/2, box.y + box.height/2);
          await page.mouse.down();
          await page.waitForTimeout(1150);
          await page.mouse.up();
        };
        await hold();
        await waitState(s => s.enterControl?.autoRunning);
        await button.click();
        await waitState(s => !s.enterControl?.autoRunning && s.enterControl?.canTap);
        const paused = (await snapshot()).revealed;
        await page.waitForTimeout(700);
        assert.equal((await snapshot()).revealed, paused);
        await page.reload();
        await page.waitForFunction(() => !document.getElementById('host-advance').disabled);
        if (process.env.HOTSTREAK_ARTIFACTS) {
          await page.screenshot({ path: path.join(process.env.HOTSTREAK_ARTIFACTS, `enter-race-${race}.png`), fullPage: true });
        }
        await hold();
        state = await waitState(s => s.phase === 'payout');
      } else if (process.env.HOTSTREAK_AUTO_RACE === '1') {
        const { spawn } = require('node:child_process');
        await new Promise((resolve, reject) => {
          const child = spawn('uv', ['run', '--python', '3.12', '--with-requirements', 'requirements.txt',
            'python', 'tests/e2e/auto-race.py'], { env: { ...process.env, PYTHONPATH: 'src' } });
          let output = '';
          child.stdout.on('data', data => { output += data; });
          child.stderr.on('data', data => { output += data; });
          child.on('error', reject);
          child.on('close', code => code === 0 ? (console.log(output.trim()), resolve()) : reject(new Error(output)));
          child.stdin.end(JSON.stringify({ origin, credentials: created }));
        });
        state = await snapshot();
      } else {
        for (let count = 0; count < 61; count++) {
          state = await advance();
          if (state.phase === 'payout') break;
        }
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
      await phoneAdvance();
      if (race === 3) {
        for (const { page } of people) await page.locator('#champion-panel').waitFor({ state: 'visible' });
        await people[0].page.reload();
        await people[0].page.locator('#champion-panel').waitFor({ state: 'visible' });
        if (process.env.HOTSTREAK_ARTIFACTS) await people[0].page.screenshot({ path: path.join(process.env.HOTSTREAK_ARTIFACTS, 'champion-phone.png'), fullPage: true });
        await phoneAdvance();
      }
    }
    for (const { page } of people) await page.waitForURL(/lobby\.html/);
    if (displayExit) {
      const result = await displayExit;
      assert.equal(result.code, 0, result.output);
      console.log(result.output.trim());
    }
    assert.deepEqual(failures, []);
    console.log('PASS: 独立した3ブラウザで参加・3レース・配当・再参加まで完了');
  } finally {
    if (enterDisplay && enterDisplay.exitCode === null) enterDisplay.kill('SIGTERM');
    await Promise.all(contexts.map(c => c.close()));
    await browser.close();
  }
})().catch(error => { console.error(error); process.exitCode = 1; });
