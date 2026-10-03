async (page) => {
  await page.goto(`file:///${process.env.WORKSPACE || '.'}/开屏动效_刀刃瞳孔转场.html`);
  await page.waitForTimeout(900);
  const times = [1.42, 1.55, 1.70, 1.90, 2.00, 2.04, 2.12, 2.22, 2.35, 2.56, 2.95];
  const clamp01 = (x) => Math.max(0, Math.min(1, x));
  const inOutQuad = (x) => x < 0.5 ? 2 * x * x : 1 - 2 * (1 - x) * (1 - x);
  const rows = {};
  const problems = [];
  for (const t of times) {
    await page.evaluate((tt) => window.__splashSeek(tt), t);
    await page.waitForTimeout(130);
    const key = t.toFixed(2).replace('.', '_');
    const row = await page.evaluate(() => {
      const g = (id) => document.getElementById(id);
      const num = (v) => parseFloat(v) || 0;
      const op = (el) => parseFloat(getComputedStyle(el).opacity);
      const mid = g('midL');
      const f = getComputedStyle(mid).filter;
      const mBr = /brightness\(([\d.]+)\)/.exec(f);
      const auxR = g('auxR');
      const num2 = (s) => parseFloat(s) || 0;
      return {
        vw: window.innerWidth, vh: window.innerHeight,
        r: num(g('irisL').style.width) / 2,
        rm: num(g('midL').style.width) / 2,
        rc: num(g('coreBrightL').style.width) / 2,
        core: num(g('coreL').style.width) / 2,
        midFilter: f,
        midBr: mBr ? parseFloat(mBr[1]) : 1,
        oI: op(g('irisL')), oM: op(mid), oC: op(g('coreBrightL')),
        /* 右辅轨右缘（裁剪线，不含 slack） */
        clipEdge: num2(auxR.style.left) + num2(auxR.style.width)
      };
    });
    /* Node 端完整重现模板公式（v23b 时间轴） */
    const vw = row.vw, vh = row.vh;
    const HALF = vw / 72, hw0 = vw / 2;
    const maxR = Math.hypot(vw, vh) / 2 + 60;
    const irisR = (tt) => {
      if (tt < 1.26) return 0;
      const uu = clamp01((tt - 1.26) / 1.30);
      const ee = 1 - (1 - uu) * (1 - uu);
      const hw = HALF + (hw0 - HALF) * ee;
      const slack = (maxR * 1.14 - hw0) * inOutQuad(clamp01((tt - 2.00) / 0.95));
      return (hw + slack) * clamp01((tt - 1.26) / 0.12);
    };
    const rE = irisR(t);
    const rmE = 0.87 * rE;
    const g0 = irisR(1.48);
    let su = clamp01((t - 1.50) / 0.70); su = su * su * (3 - 2 * su);
    const gap = g0 * (1 - 0.75 * su);
    const rcE = Math.max(0, rE - gap);
    const shE = clamp01((rmE - rcE) / 36);
    const coreE = Math.min(rcE, rmE);
    const shObs = (1 - row.midBr) / 0.14;
    const near = (a, b, eps) => Math.abs(a - b) <= eps;
    const checks = {
      r: near(row.r, rE, 1.0),
      rm: near(row.rm, rmE, 1.0),
      rc: near(row.rc, rcE, 1.0),
      core: near(row.core, coreE, 1.0),
      sh: near(shObs, shE, 0.03),
      rcLEr: rcE <= rE + 0.01,
      rm087: near(row.rm, 0.87 * row.r, 1.0)
    };
    for (const k in checks) if (!checks[k]) problems.push(key + ':' + k);
    /* 亮带可见宽度：min(rc, clipEdge-中心) - min(rm, clipEdge-中心)，追平后为正即亮带在屏内 */
    const center = row.vw / 2;
    const bandVis = Math.min(row.rc, row.clipEdge - center) - Math.min(row.rm, row.clipEdge - center);
    rows[key] = Object.assign(row, { rE, rmE, rcE, coreE, shE, shObs, bandVis, checks });
    await page.screenshot({ path: `${process.env.WORKSPACE || '.'}/.workbuddy/v23_t` + key + '.png' });
  }
  /* 终态检查：2.95s 内圈已超越次外圈且阴影彻底消失、恒不超最外圈 */
  const last = rows['2_95'];
  if (!(last.rc > last.rm)) problems.push('no-overrun-at-2.95');
  if (last.shObs > 0.02) problems.push('shadow-not-gone-at-2.95');
  if (last.rc > last.r + 0.01) problems.push('inner-exceeds-outer');
  /* 超越点存在性 */
  let overrun = false;
  for (const k in rows) if (rows[k].rc > rows[k].rm) overrun = true;
  if (!overrun) problems.push('no-overrun-anywhere');
  /* 亮带可见峰值：序列中 bandVis 最大值应 >= 15px（肉眼可辨） */
  let peak = 0;
  for (const k in rows) peak = Math.max(peak, rows[k].bandVis);
  if (peak < 15) problems.push('band-too-narrow:' + peak.toFixed(1));
  return 'V23JSON:' + JSON.stringify({ problems, peakBand: peak, rows }) + '\n```';
}
