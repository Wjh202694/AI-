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
  /* A/B 1: t=1.78 阴影峰值期 */
  await page.evaluate((tt) => window.__splashSeek(tt), 1.78);
  await page.waitForTimeout(150);
  out.shadowGeo = await page.evaluate(geo);
  out.shadowSh = await page.evaluate(() => {
    const f = getComputedStyle(document.getElementById('midR')).filter;
    const m = /brightness\(([\d.]+)\)/.exec(f);
    return m ? 1 - parseFloat(m[1]) : 0;
  });
  await page.screenshot({ path: `${process.env.WORKSPACE || '.'}/.workbuddy/v24ab_shadow_A.png` });
  await page.addStyleTag({ content: '.mid { filter: blur(3.5px) !important; }' });
  await page.waitForTimeout(120);
  await page.screenshot({ path: `${process.env.WORKSPACE || '.'}/.workbuddy/v24ab_shadow_B.png` });
  /* A/B 2: t=2.22 亮带期（reload 清除已注入样式） */
  await page.evaluate(() => location.reload());
  await page.waitForTimeout(1100);
  await page.evaluate((tt) => window.__splashSeek(tt), 2.22);
  await page.waitForTimeout(150);
  out.bandGeo = await page.evaluate(geo);
  await page.screenshot({ path: `${process.env.WORKSPACE || '.'}/.workbuddy/v24ab_band_A.png` });
  await page.addStyleTag({ content: '.core-bright { filter: none !important; }' });
  await page.waitForTimeout(120);
  await page.screenshot({ path: `${process.env.WORKSPACE || '.'}/.workbuddy/v24ab_band_B.png` });
  return 'V24AB2:' + JSON.stringify(out);
}
