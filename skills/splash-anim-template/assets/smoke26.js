async (page) => {
  const errors = [];
  page.on('pageerror', (e) => errors.push('pageerror:' + e.message));
  page.on('console', (m) => { if (m.type() === 'error') errors.push('console:' + m.text()); });
  await page.setViewportSize({ width: 1280, height: 800 });
  await page.goto(`file:///${process.env.WORKSPACE || '.'}/开屏特效_通用模板.html`);
  await page.waitForTimeout(1400);
  await page.screenshot({ path: `${process.env.WORKSPACE || '.'}/.workbuddy/smoke26_mid.png` });
  await page.waitForFunction(() => document.getElementById('splash').classList.contains('done'), null, { timeout: 12000 });
  const first = await page.evaluate(() => ({
    overflowRestored: document.body.style.overflow === '',
    splashHidden: getComputedStyle(document.getElementById('splash')).display === 'none'
  }));
  /* 重播：evaluate click（done 后 splash 已 display:none，规避 hit-test 与动画层竞态） */
  await page.evaluate(() => document.getElementById('replayBtn').click());
  await page.waitForTimeout(1500);
  const midReplay = await page.evaluate(() => {
    const s = document.getElementById('splash');
    const el = document.elementFromPoint(window.innerWidth / 2, window.innerHeight / 2);
    return { splashVisible: getComputedStyle(s).display !== 'none' && !s.classList.contains('done'), centerHit: el ? (el.id || el.className || el.tagName) : 'null' };
  });
  await page.screenshot({ path: `${process.env.WORKSPACE || '.'}/.workbuddy/smoke26_replay.png` });
  await page.waitForFunction(() => document.getElementById('splash').classList.contains('done'), null, { timeout: 12000 });
  /* 重播后 seek 验证 v26 三环公式仍生效 */
  await page.evaluate(() => window.__splashSeek(2.30));
  await page.waitForTimeout(120);
  const seekOk = await page.evaluate(() => {
    const g = (id) => document.getElementById(id);
    const num = (v) => parseFloat(v) || 0;
    const r = num(g('irisL').style.width) / 2, rm = num(g('midL').style.width) / 2, rc = num(g('coreBrightL').style.width) / 2;
    return { r, rm, rc, gapOM: +(r - rm).toFixed(1), orderOk: r > rm && rm > rc };  /* 2.30 交叉前：内圈尚未反超次外 */
  });
  return 'SMOKE26:' + JSON.stringify({ first, midReplay, seekOk, replayDone: true, errors });
}
