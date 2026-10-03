#!/usr/bin/env bash
# axe 无障碍审计（2026-09-20 实测通过：agent-browser 0.38.1 + axe-core 4.13，Windows/Git Bash）
# 链路：open → 注入 axe-core CDN → axe.run() → 输出 violations JSON
#
# 用法:
#   bash axe-audit.sh <url>
# 前提:
#   - npm i -g agent-browser（首次运行 daemon 冷启动较慢，卡住时 stop 后重试一次）
#   - 能访问 cdn.jsdelivr.net
set -euo pipefail
URL="${1:?用法: axe-audit.sh <url>}"

agent-browser open "$URL" >/dev/null

agent-browser eval '(() => { if (window.axe) return "already"; const s = document.createElement("script"); s.src = "https://cdn.jsdelivr.net/npm/axe-core/axe.min.js"; document.head.appendChild(s); return "injecting"; })()' >/dev/null
sleep 4

V=$(agent-browser eval 'window.axe ? axe.version : "not-loaded"' 2>/dev/null || echo '"err"')
if [ "$V" = '"not-loaded"' ] || [ "$V" = '"err"' ]; then
  echo "FAIL: axe 未加载（检查网络/CDN 或稍后重试）"; exit 1
fi
echo "# axe-core $V @ $URL"

agent-browser eval 'window.__res = null; axe.run().then(r => { window.__res = r; }); "started"' >/dev/null
sleep 6

agent-browser eval 'window.__res ? JSON.stringify({url: location.href, violations: window.__res.violations.map(v => ({id: v.id, impact: v.impact, help: v.help, nodes: v.nodes.length})), passes: window.__res.passes.length}, null, 1) : "PENDING（稍等几秒重跑最后一条命令）"'
