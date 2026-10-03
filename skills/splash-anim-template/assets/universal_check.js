async (page) => {
  const out = {};
  /* 1) URL 模式：关键冻结帧目检（验证 CSS 变量背景 + 涟漪引擎） */
  await page.goto(`file:///${process.env.WORKSPACE || '.'}/开屏特效_通用模板.html`);
  await page.waitForTimeout(1200);
  await page.evaluate((tt) => window.__splashSeek(tt), 1.42);
  await page.waitForTimeout(150);
  out.s142 = await page.evaluate(() => ({
    r: parseFloat(document.getElementById('irisL').style.width) / 2,
    bgApplied: getComputedStyle(document.getElementById('midL')).backgroundImage.slice(0, 30)
  }));
  await page.screenshot({ path: `${process.env.WORKSPACE || '.'}/.workbuddy/uni_t142.png` });
  await page.evaluate((tt) => window.__splashSeek(tt), 2.22);
  await page.waitForTimeout(150);
  await page.screenshot({ path: `${process.env.WORKSPACE || '.'}/.workbuddy/uni_t222.png` });
  /* 2) URL 模式自然播放 → done */
  await page.evaluate(() => location.reload());
  await page.waitForTimeout(600);
  await page.waitForFunction(() => document.getElementById('splash').classList.contains('done'), null, { timeout: 9000 });
  out.urlModeDone = true;
  await page.screenshot({ path: `${process.env.WORKSPACE || '.'}/.workbuddy/uni_site.png` });
  /* 3) 单文件版自然播放 → done */
  await page.goto(`file:///${process.env.WORKSPACE || '.'}/开屏特效_通用模板_单文件版.html`);
  await page.waitForTimeout(600);
  await page.screenshot({ path: `${process.env.WORKSPACE || '.'}/.workbuddy/uni_pack_mid.png` });
  await page.waitForFunction(() => document.getElementById('splash').classList.contains('done'), null, { timeout: 9000 });
  out.packedDone = true;
  await page.screenshot({ path: `${process.env.WORKSPACE || '.'}/.workbuddy/uni_pack_site.png` });
  return 'UNICHECK:' + JSON.stringify(out);
}
