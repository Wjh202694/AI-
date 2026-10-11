async (page) => {
  await page.setViewportSize({ width: 1920, height: 1080 });
  await page.goto(`file:///${process.env.WORKSPACE || '.'}/开屏特效_通用模板.html`);
  await page.waitForTimeout(900);
  const times = [1.30, 1.56, 1.70, 1.86, 2.00, 2.10, 2.30, 2.45, 2.69, 2.80, 2.95];
  const clamp01 = (x) => Math.max(0, Math.min(1, x));
  const ss = (x) => { x = clamp01(x); return x * x * (3 - 2 * x); };
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
      const mBr = /brightness\(([\d.]+)\)/.exec(getComputedStyle(mid).filter);
      return {
        vw: window.innerWidth, vh: window.innerHeight,
        r: num(g('irisL').style.width) / 2,
        rm: num(g('midL').style.width) / 2,
        rc: num(g('coreBrightL').style.width) / 2,
        core: num(g('coreL').style.width) / 2,
        midBr: mBr ? parseFloat(mBr[1]) : 1,
        oI: op(g('irisL')), oM: op(mid), oC: op(g('coreBrightL'))
      };
    });
    const maxR = Math.hypot(row.vw, row.vh) / 2 + 60;
    const R = maxR * 1.08;
    const uu = clamp01((t - 1.26) / 1.69);
    const ee = uu < 0.5 ? 2 * uu * uu : 1 - 2 * (1 - uu) * (1 - uu);
    const rE = R * ee;
    const rmE = rE * (1 - 0.13 * ss((t - 1.56) / 0.35));
    const kk = 0.50 - 0.42 * ss((t - 1.74) / 1.21);
    const rcE = rE * (1 - kk);
    const coreE = Math.min(rcE, rmE);
    const shE = clamp01((rmE - rcE) / 26);
    const shObs = (1 - row.midBr) / 0.14;
    const near = (a, b, eps) => Math.abs(a - b) <= eps;
    const checks = {
      r: near(row.r, rE, 1.0),
      rm: near(row.rm, rmE, 1.0),
      rc: near(row.rc, rcE, 1.0),
      core: near(row.core, coreE, 1.0),
      sh: near(shObs, shE, 0.03),
      rcLtR: rcE <= rE + 0.01,
      rmLtR: rmE <= rE + 0.01
    };
    for (const k in checks) if (!checks[k]) problems.push(key + ':' + k);
    rows[key] = Object.assign(row, { rE, rmE, rcE, coreE, shE, shObs, checks });
    if (['1_56', '2_10', '2_30', '2_80'].indexOf(key) >= 0) {
      await page.screenshot({ path: `${process.env.WORKSPACE || '.'}/.workbuddy/v26_t` + key + '.png' });
    }
  }
  const g = (k) => rows[k];
  const gapOI = (k) => g(k).rE - g(k).rcE;
  const gapMI = (k) => g(k).rmE - g(k).rcE;
  const gapOM = (k) => g(k).rE - g(k).rmE;
  /* 1) 外-次间距：t<1.60 次外圈未张开（gap=0）允许非降；1.70 起严格单调增 */
  let prev = -1;
  for (const t of times) {
    const k = t.toFixed(2).replace('.', '_');
    const gp = gapOM(k);
    if (t < 1.60) { if (gp < prev - 1e-9) problems.push('OM-decreasing@' + k); }
    else if (gp <= prev + 1e-9) problems.push('OM-not-increasing@' + k);
    prev = gp;
  }
  /* 2) 外-内间距：恒正、峰值落在 2.10-2.45 窗口（2.30 最大）、先增后减 */
  for (const t of times) { const k = t.toFixed(2).replace('.', '_'); if (!(gapOI(k) > 0)) problems.push('OI-nonpositive@' + k); }
  if (!(gapOI('2_30') >= gapOI('2_10') && gapOI('2_30') >= gapOI('2_45'))) problems.push('OI-peak-out-of-window');
  if (!(gapOI('2_30') > gapOI('1_86') && gapOI('2_30') > gapOI('2_95'))) problems.push('OI-not-rise-fall');
  if (!(gapOI('2_30') > gapOI('1_86') * 1.5)) problems.push('OI-peak-not-big:' + gapOI('2_30').toFixed(0) + 'vs' + gapOI('1_86').toFixed(0));
  /* 3) 次-内间距：先增（2.10>1.86）后减、≈2.69 穿一次（2.80/2.95 为负且 2.45 前为正） */
  if (!(gapMI('2_10') > gapMI('1_86'))) problems.push('MI-not-rising-early');
  if (!(Math.abs(gapMI('2_69')) < 3)) problems.push('MI-cross-not-at-2.69:' + gapMI('2_69').toFixed(1));
  if (!(gapMI('2_80') < 0 && gapMI('2_95') < 0)) problems.push('MI-not-negative-after-cross');
  for (const k of ['1_86', '2_00', '2_10', '2_30', '2_45']) { if (!(gapMI(k) > 0)) problems.push('MI-not-positive@' + k); }
  /* 4) 错峰淡入：1.30 仅外圈可见；1.56 次外圈出生（oM=0）；1.70 次外已显内圈未显；1.86 内圈出生 */
  if (!(g('1_30').oI > 0.2 && g('1_30').oM === 0 && g('1_30').oC === 0)) problems.push('stagger-outer-only:' + g('1_30').oI + '/' + g('1_30').oM + '/' + g('1_30').oC);
  if (!(g('1_56').oM === 0 && g('1_56').oI > 0.9)) problems.push('stagger-mid-birth:' + g('1_56').oM);
  if (!(g('1_70').oM > 0.9 && g('1_70').oC === 0)) problems.push('stagger-mid-only:' + g('1_70').oM + '/' + g('1_70').oC);
  if (!(g('1_86').oC === 0 && g('2_00').oC > 0.9)) problems.push('stagger-inner-birth:' + g('1_86').oC);
  /* 5) 阴影：交叉前可感知、交叉后归零 */
  if (!(g('2_10').shObs > 0.3 && g('2_30').shObs > 0.3)) problems.push('shadow-too-weak:' + g('2_10').shObs.toFixed(2) + '/' + g('2_30').shObs.toFixed(2));
  for (const k of ['2_80', '2_95']) { if (g(k).shObs > 0.05) problems.push('shadow-residue@' + k + ':' + g(k).shObs.toFixed(3)); }
  /* 6) 终态：2.95 三环序 r > rc > rm，亮带宽 ≥40px，r 全出屏 */
  if (!(g('2_95').rE > g('2_95').rcE && g('2_95').rcE > g('2_95').rmE)) problems.push('final-order-wrong');
  const bandW = g('2_95').rcE - g('2_95').rmE;
  if (!(bandW >= 40)) problems.push('band-narrow@2.95:' + bandW.toFixed(1));
  const maxR = Math.hypot(g('2_95').vw, g('2_95').vh) / 2 + 60;
  if (!(g('2_95').rE >= maxR)) problems.push('not-fully-out@2.95');
  /* 7) 速度连续性：r 主曲线 + 两条间距曲线稠密采样无跳变 */
  const vwav = g('2_95').vw, vhav = g('2_95').vh;
  const RV = (tt) => { const u = clamp01((tt - 1.26) / 1.69); const e = u < 0.5 ? 2 * u * u : 1 - 2 * (1 - u) * (1 - u); return (Math.hypot(vwav, vhav) / 2 + 60) * 1.08 * e; };
  const RMV = (tt) => RV(tt) * (1 - 0.13 * ss((tt - 1.56) / 0.35));
  const RCV = (tt) => RV(tt) * (1 - (0.50 - 0.42 * ss((tt - 1.74) / 1.21)));
  const jump = (F, lo, hi) => { let J = 0, Jat = 0, pv = null; for (let tt = lo; tt <= hi; tt += 0.01) { const v = (F(tt + 0.005) - F(tt - 0.005)) / 0.01; if (pv !== null && Math.abs(v - pv) > J) { J = Math.abs(v - pv); Jat = tt; } pv = v; } return { J, Jat }; };
  const jR = jump(RV, 1.27, 2.94), jOM = jump((x) => RV(x) - RMV(x), 1.27, 2.94), jMI = jump((x) => RMV(x) - RCV(x), 1.27, 2.94);
  if (jR.J > 35) problems.push('vel-jump-r:' + jR.J.toFixed(1) + '@' + jR.Jat.toFixed(2));
  if (jOM.J > 60) problems.push('vel-jump-om:' + jOM.J.toFixed(1) + '@' + jOM.Jat.toFixed(2));
  if (jMI.J > 60) problems.push('vel-jump-mi:' + jMI.J.toFixed(1) + '@' + jMI.Jat.toFixed(2));
  return 'V26JSON:' + JSON.stringify({ problems, peakOI: +gapOI('2_30').toFixed(1), peakMI: +Math.max(...times.map((t) => gapMI(t.toFixed(2).replace('.', '_')))).toFixed(1), bandW: +bandW.toFixed(1), jR: +jR.J.toFixed(1), jOM: +jOM.J.toFixed(1), jMI: +jMI.J.toFixed(1), rows }) + '\n```';
}
