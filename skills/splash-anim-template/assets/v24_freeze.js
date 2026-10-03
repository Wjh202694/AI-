async (page) => {
  await page.goto(`file:///${process.env.WORKSPACE || '.'}/开屏动效_刀刃瞳孔转场.html`);
  await page.waitForTimeout(900);
  const times = [1.30, 1.35, 1.42, 1.55, 1.70, 1.78, 1.85, 2.00, 2.10, 2.22, 2.35, 2.56, 2.95];
  const clamp01 = (x) => Math.max(0, Math.min(1, x));
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
        clipEdge: num2(auxR.style.left) + num2(auxR.style.width)
      };
    });
    /* Node 端完整重现 v24 涟漪公式 */
    const vw = row.vw, vh = row.vh;
    const maxR = Math.hypot(vw, vh) / 2 + 60;
    const irisR = (tt) => {
      if (tt < 1.26) return 0;
      const uu = clamp01((tt - 1.26) / 1.69);
      const ee = uu < 0.5 ? 2 * uu * uu : 1 - 2 * (1 - uu) * (1 - uu);
      return maxR * 1.08 * ee;
    };
    const rE = irisR(t);
    const rmE = 0.87 * rE;
    let ks = clamp01((t - 1.30) / 1.05); ks = ks * ks * (3 - 2 * ks);
    const kk = 0.46 - 0.43 * ks;
    const rcE = rE * (1 - kk);
    const shE = clamp01((rmE - rcE) / 26);
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
    /* 亮带可见宽度（水平轴向，裁剪内） */
    const center = row.vw / 2;
    const bandVis = Math.min(row.rc, row.clipEdge - center) - Math.min(row.rm, row.clipEdge - center);
    rows[key] = Object.assign(row, { rE, rmE, rcE, coreE, shE, shObs, bandVis, checks });
    await page.screenshot({ path: `${process.env.WORKSPACE || '.'}/.workbuddy/v24_t` + key + '.png' });
  }
  /* --- v24 特征断言 --- */
  const g = (k) => rows[k];
  /* 1) 慢起步：1.30s 半径 <3px（很小的点）；1.42s 仍在 8-20px（非大圆突现） */
  if (!(g('1_30').rE < 3)) problems.push('not-tiny-dot-at-1.30:' + g('1_30').rE.toFixed(1));
  if (!(g('1_42').rE >= 8 && g('1_42').rE <= 20)) problems.push('slow-start-range:' + g('1_42').rE.toFixed(1));
  /* 2) 外圈-次外圈间距 0.13r 严格单调增 */
  let prevGap = -1;
  for (const t of times) {
    const k = t.toFixed(2).replace('.', '_');
    const gap = g(k).rE - g(k).rmE;
    if (gap <= prevGap + 1e-9) problems.push('gap-not-increasing@' + k);
    prevGap = gap;
  }
  /* 3) 阴影期（≤1.85s）rc<rm 且阴影可感知；亮带期（≥2.10s）rc>rm 且阴影归零 */
  for (const k of ['1_55', '1_70', '1_78', '1_85']) {
    if (!(g(k).rcE < g(k).rmE)) problems.push('shadow-phase-rc>=rm@' + k);
  }
  if (!(g('1_70').shObs > 0.3 && g('1_78').shObs > 0.3)) problems.push('shadow-too-weak:' + g('1_70').shObs.toFixed(2) + '/' + g('1_78').shObs.toFixed(2));
  for (const k of ['2_10', '2_22', '2_35', '2_56', '2_95']) {
    if (!(g(k).rcE > g(k).rmE)) problems.push('band-phase-rc<=rm@' + k);
    if (g(k).shObs > 0.03) problems.push('shadow-residue@' + k + ':' + g(k).shObs.toFixed(3));
  }
  /* 4) 追平点在 1.85~2.10 之间 */
  if (!(g('1_85').rcE < g('1_85').rmE && g('2_10').rcE > g('2_10').rmE)) problems.push('catchup-out-of-window');
  /* 5) 亮带随涟漪渐宽：2.35s 带宽 ≥40px；可见峰值 ≥25px */
  const bandW = g('2_35').rcE - g('2_35').rmE;
  if (!(bandW >= 40)) problems.push('band-narrow@2.35:' + bandW.toFixed(1));
  let peak = 0;
  for (const k in rows) peak = Math.max(peak, rows[k].bandVis);
  if (peak < 25) problems.push('bandVis-too-narrow:' + peak.toFixed(1));
  /* 6) 终态：2.95s r≥maxR（全出屏）、阴影归零 */
  const vw = rows['2_95'].vw, vh = rows['2_95'].vh;
  const maxR = Math.hypot(vw, vh) / 2 + 60;
  if (!(g('2_95').rE >= maxR)) problems.push('not-fully-out@2.95:' + g('2_95').rE.toFixed(0) + '<' + maxR.toFixed(0));
  if (g('2_95').shObs > 0.02) problems.push('shadow-not-gone-at-2.95');
  /* 7) 速度连续性（公式稠密采样）：全时段无速度跳变（旧版 ramp 末端 1.38s / slack 起点 2.00s 两处断崖已消除）
        inOutQuad 在 u=0.5（t≈2.105s）加速度变号，单步 Δv 理论上限 ≈22px/s；v23 断崖处 Δv≈850px/s */
  const irisR2 = (tt) => {
    if (tt < 1.26) return 0;
    const uu = clamp01((tt - 1.26) / 1.69);
    const ee = uu < 0.5 ? 2 * uu * uu : 1 - 2 * (1 - uu) * (1 - uu);
    return (Math.hypot(vw, vh) / 2 + 60) * 1.08 * ee;
  };
  let J = 0, Jat = 0, prevV = null;
  for (let tt = 1.27; tt <= 2.94; tt += 0.01) {
    const v = (irisR2(tt + 0.005) - irisR2(tt - 0.005)) / 0.01;
    if (prevV !== null && Math.abs(v - prevV) > J) { J = Math.abs(v - prevV); Jat = tt; }
    prevV = v;
  }
  if (J > 35) problems.push('velocity-jump:' + J.toFixed(1) + 'px/s@' + Jat.toFixed(2));
  const vSlow = (irisR2(1.28) - irisR2(1.27)) / 0.01;
  if (!(vSlow < 20)) problems.push('start-not-slow:' + vSlow.toFixed(1) + 'px/s');
  return 'V24JSON:' + JSON.stringify({ problems, peakBand: peak, bandW235: bandW, velJ: J, velJat: Jat, rows }) + '\n```';
}
