# -*- coding: utf-8 -*-
"""v24 -> v25 全局提速补丁：SPEED 因子（提速 20%，整场感知 ≈3 秒级）
原则：只在 t 计算唯一入口缩放，所有相位常量不动（等比压缩、曲线连续性不破坏）；
__splashSeek 参数保持「时间轴秒」语义（与相位常量同域）→ 验证脚本零改动。
"""
import os
import pathlib, shutil

P = pathlib.Path(os.environ["WORKSPACE"]) / ".workbuddy/splash_template.html"
bak = P.with_suffix(".html.v24.bak")
if not bak.exists():
    shutil.copy2(P, bak)
src = P.read_text(encoding="utf-8")
n0 = len(src)

def rep(old, new, tag):
    global src
    assert src.count(old) == 1, f"{tag}: anchor x{src.count(old)}"
    src = src.replace(old, new)

# 1) SPEED 常量（挂在 raf 状态声明前）
rep("  var raf = null, t0 = 0, played = false, finished = true;",
    "  var SPEED = 0.8;   /* 全局速度：<1 加速（0.8=提速 20%）。时间轴唯一缩放入口，所有相位等比压缩 */\n"
    "  var raf = null, t0 = 0, played = false, finished = true;", "SPEED")

# 2) t 计算入口
rep("    var t = (now - t0) / 1000;",
    "    var t = (now - t0) / 1000 * SPEED;   /* 全局速度入口：缩放后 t 与各相位常量同域 */", "t-entry")

# 3) seek 语义保持「时间轴秒」
rep("    t0 = performance.now() - t * 1000;",
    "    t0 = performance.now() - (t / SPEED) * 1000;   /* seek 参数=时间轴秒（相位常量同域），不随 SPEED 改变 */", "seek")

# 4) finish 缓冲：vanish(3.08s)+CSS 淡出 0.65s 后留余量（缩放后 3.80s 收尾）
rep("    if (t >= 4.65) { finish(); return; }",
    "    if (t >= 4.75) { finish(); return; }   /* 缩放后=3.80s：vanish(3.08)+淡出0.65s 完成后再收尾 */", "finish")

# 5) 音效速率匹配加速
rep("      try { sfx.currentTime = 0; sfx.volume = 0.55; sfx.play(); } catch (e) {}",
    "      try { sfx.currentTime = 0; sfx.volume = 0.55; sfx.playbackRate = 1 / SPEED; sfx.play(); } catch (e) {}", "sfx")

assert src.count("SPEED") >= 5
P.write_text(src, encoding="utf-8")
print("PATCH OK  bytes:", n0, "->", len(src))
print("backup:", bak)
