# -*- coding: utf-8 -*-
"""v23 A/B 对比 v2：按 getBoundingClientRect 渲染几何采样（world scale 1.07 校正）
阴影帧 t=1.70: 圆心(519.4,462.0) coreR=162.9 mR=276.4
亮带帧 t=2.22: 圆心(516.1,459.2) coreR=482.9 cbR=509.6
"""
from PIL import Image
import statistics, json

DPR = 1.5

def band_ratio(fnA, fnB, cx, cy, dx_lo, dx_hi, half_band=6, step=1):
    imA = Image.open(fnA).convert('RGB')
    imB = Image.open(fnB).convert('RGB')
    pa, pb = imA.load(), imB.load()
    out = []
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
            out.append((dx, ma / mb))
    return out

def summarize(tag, prof, lo, hi):
    vals = [v for _, v in prof]
    med, mn, mx = statistics.median(vals), min(vals), max(vals)
    ok = lo <= med <= hi and mn > lo - 0.06 and mx < hi + 0.06
    print('%-14s median=%.3f min=%.3f max=%.3f  期望[%.2f,%.2f]  %s' %
          (tag, med, mn, mx, lo, hi, 'PASS' if ok else 'FAIL'))
    return ok

g = json.loads('''{"shadowGeo":{"cbR":{"cx":519.39,"cy":461.95,"r":162.85},"cR":{"cx":519.39,"cy":461.95,"r":162.85},"mR":{"cx":519.39,"cy":461.95,"r":276.42}},"bandGeo":{"cbR":{"cx":516.12,"cy":459.18,"r":509.59},"cR":{"cx":516.12,"cy":459.18,"r":482.91}}}''')

sg, bg = g['shadowGeo'], g['bandGeo']
print('=== 阴影 A/B  t=1.70 (渲染几何) ===')
r_mid = band_ratio('v23ab2_shadow_A.png', 'v23ab2_shadow_B.png', sg['mR']['cx'], sg['mR']['cy'],
                   sg['cR']['r'] + 12, sg['mR']['r'] - 12)
r_ctrl = band_ratio('v23ab2_shadow_A.png', 'v23ab2_shadow_B.png', sg['cR']['cx'], sg['cR']['cy'],
                    60, sg['cR']['r'] - 40)
ok1 = summarize('mid带 A/B', r_mid, 0.80, 0.92)
ok2 = summarize('对照区 A/B', r_ctrl, 0.96, 1.04)

print('=== 亮带 A/B  t=2.22 (渲染几何) ===')
r_band = band_ratio('v23ab2_band_A.png', 'v23ab2_band_B.png', bg['cbR']['cx'], bg['cbR']['cy'],
                    bg['cR']['r'] + 8, bg['cbR']['r'] - 8)
r_ctrl2 = band_ratio('v23ab2_band_A.png', 'v23ab2_band_B.png', bg['cbR']['cx'], bg['cbR']['cy'],
                     300, 460)
ok3 = summarize('亮带 A/B  ', r_band, 1.06, 1.18)
ok4 = summarize('对照区 A/B', r_ctrl2, 0.96, 1.04)

# rm 边界过渡：coreR 渲染缘附近 ±8px（期望比值从 1.0 平滑过渡，无 <0.95 深谷）
r_edge = band_ratio('v23ab2_band_A.png', 'v23ab2_band_B.png', bg['cbR']['cx'], bg['cbR']['cy'],
                    bg['cR']['r'] - 8, bg['cR']['r'] + 8)
vals = [v for _, v in r_edge]
ok5 = min(vals) > 0.95
print('rm边界过渡    min=%.3f  %s' % (min(vals), 'PASS' if ok5 else 'FAIL'))

print('=' * 44)
print('A/B CHECKS v2:', 'ALL PASS' if all([ok1, ok2, ok3, ok4, ok5]) else 'SOME FAILED')
