async (page) => {
  await page.goto(`file:///${process.env.WORKSPACE || '.'}/开屏动效_刀刃瞳孔转场.html`);
  await page.waitForTimeout(900);
  const geo = () => {
    const r = (id) => { const b = document.getElementById(id).getBoundingClientRect();
      return { cx: b.left + b.width / 2, cy: b.top + b.height / 2, r: b.width / 2 }; };
    return { cbR: r('coreBrightR'), cR: r('coreR'), mR: r('midR'), clipR: (() => {
      const b = document.getElementById('irisClipR').getBoundingClientRect();
      return { left: b.left, top: b.top, right: b.right, bottom: b.bottom }; })() };
  };
  const out = {};
  /* A/B 1: t=1.70 阴影 */
  await page.evaluate((tt) => window.__splashSeek(tt), 1.70);
  await page.waitForTimeout(150);
  out.shadowGeo = await page.evaluate(geo);
  await page.screenshot({ path: `${process.env.WORKSPACE || '.'}/.workbuddy/v23ab2_shadow_A.png` });
  await page.addStyleTag({ content: '.mid { filter: blur(3.5px) !important; }' });
  await page.waitForTimeout(120);
  await page.screenshot({ path: `${process.env.WORKSPACE || '.'}/.workbuddy/v23ab2_shadow_B.png` });
  /* A/B 2: t=2.22 亮带 */
  await page.evaluate(() => location.reload());
  await page.waitForTimeout(1100);
  await page.evaluate((tt) => window.__splashSeek(tt), 2.22);
  await page.waitForTimeout(150);
  out.bandGeo = await page.evaluate(geo);
  await page.screenshot({ path: `${process.env.WORKSPACE || '.'}/.workbuddy/v23ab2_band_A.png` });
  await page.addStyleTag({ content: '.core-bright { filter: none !important; }' });
  await page.waitForTimeout(120);
  await page.screenshot({ path: `${process.env.WORKSPACE || '.'}/.workbuddy/v23ab2_band_B.png` });
  return 'V23AB2:' + JSON.stringify(out);
}
