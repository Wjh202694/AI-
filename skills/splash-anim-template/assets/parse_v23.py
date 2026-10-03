# -*- coding: utf-8 -*-
"""解析 playwright-cli 输出中的 V23JSON（处理 JS 风格转义显示）"""
import json, sys

fn = sys.argv[1] if len(sys.argv) > 1 else 'v23_out2.txt'
raw = open(fn, encoding='utf-8', errors='replace').read()
i = raw.find('V23JSON:')
txt = raw[i + 8:]
# 去掉可能的前导空白/反引号围栏
txt = txt.lstrip()
if txt.startswith('`'):
    txt = txt.lstrip('`').lstrip()
# 文件中的引号被转义为 \" （JS 字符串显示风格），还原
txt = txt.replace('\\"', '"')
d, _ = json.JSONDecoder().raw_decode(txt.lstrip())

print('PROBLEMS:', d['problems'] if d['problems'] else 'NONE - all checks passed')
print('peakBand: %.1f px' % d['peakBand'])
print()
print('%-6s %7s %7s %7s %7s %6s | %6s %6s | %7s %s' % ('t', 'r', 'rm', 'rc', 'core', 'shE', 'shObs', 'bandVis', 'clipEdge', 'ok'))
for k, v in d['rows'].items():
    print('%-6s %7.1f %7.1f %7.1f %7.1f %6.2f | %6.3f %6.3f | %7.1f %s' % (
        k, v['r'], v['rm'], v['rc'], v['core'], v['shE'], v['shObs'], v['bandVis'], v['clipEdge'],
        all(v['checks'].values())))
