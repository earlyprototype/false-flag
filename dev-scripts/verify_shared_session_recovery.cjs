const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const { chromium } = require(process.argv[2] || 'playwright');
const base = 'http://127.0.0.1:8017';
const evidenceDir = path.resolve(process.argv[3] || path.join(__dirname, 'play-verify', 'shared-session-recovery'));
fs.mkdirSync(evidenceDir, { recursive: true });

(async () => {
  const browser = await chromium.launch({ headless: true });
  try {
    const context = await browser.newContext({ viewport: { width: 1440, height: 1000 } });
    const routingResponse = await context.request.get(base + '/routing');
    assert.equal(routingResponse.status(), 200, 'Cannot verify mock routing');
    const routing = await routingResponse.json();
    assert.equal(routing.provider, 'mock', 'Start the API with WARGAME_LLM=mock');
    assert.ok(routing.contexts.length && routing.contexts.every(row => row.effective_provider === 'mock'),
      'All runtime routing overrides must use mock');
    const dashboard = await context.newPage();
    const dataflow = await context.newPage();
    const globe = await context.newPage();
    const pages = { dashboard, dataflow, globe };
    const errors = [];
    const streamRequests = { dashboard: 0, dataflow: 0, globe: 0 };
    for (const [name, page] of Object.entries(pages)) {
      page.on('pageerror', error => errors.push({ page: name, message: error.message }));
      page.on('request', request => {
        if (request.url().startsWith(base + '/stream/')) streamRequests[name] += 1;
      });
    }
    const post = async (route, data = {}) => {
      const response = await context.request.post(base + route, { data });
      assert.equal(response.status(), 200, route + ': ' + await response.text());
      return response.json();
    };
    await dashboard.goto(base + '/dashboard?proof=recovery#keep');
    await dashboard.locator('#btnNew').click();
    await dashboard.waitForFunction(() => !!document.querySelector('#sessionInput').value);
    const id = await dashboard.locator('#sessionInput').inputValue();
    assert.ok(new URL(dashboard.url()).searchParams.get('game') === id);
    await dataflow.goto(base + '/dataflow?proof=recovery#keep');
    await dataflow.locator('#sessInput').fill(id);
    await dataflow.locator('#attachBtn').click();
    await dataflow.waitForFunction(id => new URL(location.href).searchParams.get('game') === id, id);
    await globe.goto(base + '/globe?proof=recovery#keep');
    await globe.locator('#sessionInput').fill(id);
    await globe.locator('#btnAttach').click();
    await globe.waitForFunction(id => new URL(location.href).searchParams.get('game') === id, id);
    console.log('All three pages attached to ' + id);

    const playTurn = async (later = false) => {
      if (later) await post('/game/' + id + '/briefing');
      await post('/game/' + id + '/briefing/ack');
      let state = await (await context.request.get(base + '/game/' + id)).json();
      if (state.active_call) {
        await post('/game/action/diplomacy/reply', {
          session_id: id, message: 'We will consult allies and seek independent verification before escalation.'
        });
        await post('/game/action/diplomacy/reply', { session_id: id, message: '/end' });
      }
      await post('/game/discussion', {
        session_id: id, advisor: 'all', question: 'What can we verify, and what steps protect civilians while avoiding escalation?'
      });
      const decision = { session_id: id, action_text: 'Maintain defensive readiness, consult NATO allies, and seek independent verification before further escalation.' };
      const preview = await post('/game/decision/interpret', decision);
      assert.ok(preview.interpretation);
      await post('/game/decision/commit', { ...decision, user_choice: 'confirm' });
      state = await (await context.request.get(base + '/game/' + id)).json();
      await dataflow.waitForFunction(turn => document.querySelector('#turnBadge').textContent === 'turn ' + turn, state.turn);
      await globe.waitForFunction(turn => document.querySelector('#statusBody').textContent.includes('turn ' + turn), state.turn);
      await dashboard.waitForFunction(turn => document.querySelector('#ledger').textContent.includes('TURN ' + turn + ' COMPLETE'), state.turn);
      return { turn: state.turn, phase: state.phase };
    };
    const afterTurn = await playTurn();
    assert.equal(afterTurn.turn, 2);
    console.log('Turn one adjudicated; all pages received turn two');

    for (const page of Object.values(pages)) await page.reload();
    await dashboard.waitForFunction(() => source?.readyState === EventSource.OPEN);
    await dataflow.waitForFunction(() => es?.readyState === EventSource.OPEN);
    await globe.waitForFunction(() => source?.readyState === EventSource.OPEN && !!lastRenderedTheatre);
    const restored = {};
    for (const [name, page] of Object.entries(pages)) {
      assert.equal(new URL(page.url()).searchParams.get('game'), id);
      assert.equal(new URL(page.url()).searchParams.get('proof'), 'recovery');
      assert.equal(new URL(page.url()).hash, '#keep');
      restored[name] = await page.evaluate(() => ({ sessionId, url: location.href }));
      assert.equal(restored[name].sessionId, id);
    }
    restored.dataflow.turnBadge = await dataflow.locator('#turnBadge').textContent();
    restored.globe.status = await globe.locator('#statusBody').innerText();
    const beforeReconnect = { ...streamRequests };
    for (const [name, page] of Object.entries(pages)) {
      let cutOnce = false;
      await page.route(base + '/stream/**', async route => {
        if (cutOnce) return route.continue();
        cutOnce = true;
        // A finite SSE response ends the connection; Chromium must reconnect itself.
        await route.fulfill({ status: 200, contentType: 'text/event-stream', body: ': interrupted stream\n\n' });
      });
      const retried = page.waitForResponse(response =>
        response.url().startsWith(base + '/stream/') &&
        streamRequests[name] >= beforeReconnect[name] + 2);
      await page.reload();
      await retried;
    }
    await dashboard.waitForFunction(() => source?.readyState === EventSource.OPEN);
    await dataflow.waitForFunction(() => es?.readyState === EventSource.OPEN);
    await globe.waitForFunction(() => source?.readyState === EventSource.OPEN);
    for (const [name, page] of Object.entries(pages)) {
      assert.ok(streamRequests[name] >= beforeReconnect[name] + 2, name + ' did not reconnect');
      assert.equal(await page.evaluate(() => sessionId), id);
    }
    console.log('Reload and automatic retry after an interrupted SSE response retained the same session');
    const afterReconnect = await playTurn(true);
    assert.equal(afterReconnect.turn, 3);
    for (const [name, page] of Object.entries(pages)) {
      await page.screenshot({ path: path.join(evidenceDir, name + '.png') });
    }

    const missingSessions = [];
    for (const hadStreamReady of [false, true]) {
      const missing = await context.newPage();
      missing.on('pageerror', error => errors.push({ page: 'missing-session', message: error.message }));
      const missingId = id + '-missing-' + hadStreamReady;
      const result = { hadStreamReady, streamRequests: 0, existenceProbes: 0 };
      await missing.route(base + '/stream/' + missingId + '/facilitator', route => {
        result.streamRequests += 1;
        if (result.streamRequests <= 5)
          return route.fulfill({ status: 200, contentType: 'text/event-stream',
            body: hadStreamReady ? 'event: stream_ready\ndata: {"viewer":"public"}\n\n' : ': interrupted\n\n' });
        return route.continue();
      });
      await missing.route(base + '/game/' + missingId, route => {
        result.existenceProbes += 1;
        return !hadStreamReady && result.existenceProbes <= 5 ? route.abort() : route.continue();
      });
      await missing.goto(base + '/dataflow?proof=recovery&game=' + missingId + '#keep');
      await missing.waitForFunction(() => sessionId === null && !new URL(location.href).searchParams.has('game'));
      assert.equal(result.streamRequests, 6);
      assert.equal(result.existenceProbes, hadStreamReady ? 1 : 6);
      assert.equal(await missing.locator('#sessInput').inputValue(), '');
      assert.equal(new URL(missing.url()).searchParams.get('proof'), 'recovery');
      assert.equal(new URL(missing.url()).hash, '#keep');
      missingSessions.push(result);
    }
    assert.deepEqual(errors, []);
    console.log('Real API 404 cleared missing sessions both before and after stream readiness');

    const evidence = { sessionId: id, provider: routing.provider, reconnectFault: 'closed first SSE response; automatic retry reaches real API', afterTurn, restored, afterReconnect, streamRequests, missingSessions, pageErrors: errors };
    fs.writeFileSync(path.join(evidenceDir, 'browser-result.json'), JSON.stringify(evidence, null, 2) + '\n');
    console.log(JSON.stringify(evidence, null, 2));
  } finally {
    await browser.close();
  }
})().catch(error => { console.error(error); process.exitCode = 1; });
