async (page) => {
  await page.goto(`file:///${process.env.WORKSPACE || '.'}/开屏动效_刀刃瞳孔转场.html`);
  await page.waitForTimeout(800);
  await page.screenshot({ path: `${process.env.WORKSPACE || '.'}/.workbuddy/smoke16_mid.png` });
  await page.waitForFunction(() => document.getElementById('splash').classList.contains('done'), null, { timeout: 9000 });
  const s1 = true;
  await page.screenshot({ path: `${process.env.WORKSPACE || '.'}/.workbuddy/smoke16_site.png` });
  await page.click('#replayBtn');
  await page.waitForTimeout(700);
  const hit = await page.evaluate(() => {
    const el = document.elementFromPoint(window.innerWidth/2, window.innerHeight/2);
    return el ? (el.className || el.id || el.tagName) : 'null';
  });
  const clipOk = await page.evaluate(() => {
    const c = document.getElementById('irisClipL'), a = document.getElementById('auxL');
    return Math.abs(parseFloat(c.style.width) - parseFloat(a.style.width)) < 0.5;
  });
  await page.waitForFunction(() => document.getElementById('splash').classList.contains('done'), null, { timeout: 9000 });
  return 'SMOKE16:' + JSON.stringify({ splashDoneAfterFirst: s1, centerElDuringReplay: hit, clipSyncedDuringReplay: clipOk, splashDoneAfterReplay: true });
}
