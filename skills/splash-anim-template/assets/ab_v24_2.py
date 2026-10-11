# -*- coding: utf-8 -*-
"""v24 A/B 像素对比：按 getBoundingClientRect 渲染几何采样（world scale 1.07 校正）
用法: python ab_v24_2.py < playwright 输出文件
阴影帧 t=1.78: 期望 mid带 A/B ≈ 1 - 0.14·shE(1.78)（实测 sh≈0.836 → ≈0.883）
亮带帧 t=2.22: 期望 core-bright A/B ≈ 1.12
"""
import sys, json
from PIL import Image
import statistics

DPR = 1.5

raw = sys.stdin.read()
payload = raw.split('V24AB2:', 1)[1]
payload = payload.replace('\\"', '"')
payload = payload.split('\n```')[0]
dec = json.JSONDecoder()
out, _ = dec.raw_decode(payload.strip())

def band_ratio(fnA, fnB, cx, cy, dx_lo, dx_hi, half_band=6, step=1):
    imA = Image.open(fnA).convert('RGB')
    imB = Image.open(fnB).convert('RGB')
    pa, pb = imA.load(), imB.load()
    vals = []
    for dx in range(int(dx_lo), int(dx_hi) + 1, step):
        X = int((cx + dx) * DPR)
        va, vb = [], []
        for Y in range(int((cy - half_band) * DPR), int((cy + half_band) * DPR)):
            r, g, b = pa[X, Y]
            va.append(0.299 * r + 0.587 * g + 0.114 * b)
            r, g, b = pb[X, Y]
            vb.append(0.299 * r + 0.587 * g + 0.114 * b)
        ma, mb = statistics.median(va), statistics.median(vb)
        if mb > 8:
            vals.append((dx, ma / mb))
    return vals

def summarize(tag, prof, lo, hi):
    vals = [v for _, v in prof]
    med, mn, mx = statistics.median(vals), min(vals), max(vals)
    ok = lo <= med <= hi and mn > lo - 0.06 and mx < hi + 0.06
    print('%-14s median=%.3f min=%.3f max=%.3f  期望[%.2f,%.2f]  %s' %
          (tag, med, mn, mx, lo, hi, 'PASS' if ok else 'FAIL'))
    return ok

sg = out['shadowGeo']
shE = out.get('shadowSh', 0.14)
expect = 1 - shE
print('=== 阴影 A/B  t=1.78 (sh=%.3f → 期望比率≈%.3f) ===' % (shE, expect))
r_mid = band_ratio('v24ab_shadow_A.png', 'v24ab_shadow_B.png', sg['mR']['cx'], sg['mR']['cy'],
                   sg['cR']['r'] + 4, sg['mR']['r'] - 4)
r_ctrl = band_ratio('v24ab_shadow_A.png', 'v24ab_shadow_B.png', sg['cR']['cx'], sg['cR']['cy'],
                    30, sg['cR']['r'] - 12)
ok1 = summarize('mid带 A/B', r_mid, expect - 0.05, expect + 0.05)
ok2 = summarize('对照区 A/B', r_ctrl, 0.96, 1.04)

bg = out['bandGeo']
print('=== 亮带 A/B  t=2.22 (渲染几何) ===')
r_band = band_ratio('v24ab_band_A.png', 'v24ab_band_B.png', bg['cbR']['cx'], bg['cbR']['cy'],
                    bg['cR']['r'] + 8, bg['cbR']['r'] - 8)
r_ctrl2 = band_ratio('v24ab_band_A.png', 'v24ab_band_B.png', bg['cbR']['cx'], bg['cbR']['cy'],
                     250, bg['cR']['r'] - 30)
ok3 = summarize('亮带 A/B  ', r_band, 1.06, 1.18)
ok4 = summarize('对照区 A/B', r_ctrl2, 0.96, 1.04)

# rm 边界过渡：coreR 渲染缘附近 ±8px（期望比值平滑过渡，无 <0.95 深谷）
r_edge = band_ratio('v24ab_band_A.png', 'v24ab_band_B.png', bg['cbR']['cx'], bg['cbR']['cy'],
                    bg['cR']['r'] - 8, bg['cR']['r'] + 8)
vals = [v for _, v in r_edge]
ok5 = min(vals) > 0.95 if vals else False
print('rm边界过渡    min=%.3f  %s' % (min(vals) if vals else -1, 'PASS' if ok5 else 'FAIL'))

print('=' * 44)
print('A/B CHECKS v24:', 'ALL PASS' if all([ok1, ok2, ok3, ok4, ok5]) else 'SOME FAILED')
