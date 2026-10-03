# -*- coding: utf-8 -*-
"""v25 演示模板 -> 开屏特效_通用模板.html（无音效版）
转换：__BG__×8 → CSS 变量 var(--bg)（CONFIG.bgImage 单点换图）、
文档注释 + CONFIG 配置区 + showSkip 开关。引擎/验证逻辑零改动。
2.2.0：音效已整体移除（CONFIG 不再有 sfxUrl，音频元素不再生成）。
"""
import os
import pathlib

SRC = pathlib.Path(os.environ["WORKSPACE"]) / ".workbuddy/splash_template.html"
DST = pathlib.Path(os.environ["WORKSPACE"]) / "开屏特效_通用模板.html"
src = SRC.read_text(encoding="utf-8")
n0 = len(src)
assert "sfx" not in src and "__SFX__" not in src, "源模板仍含音效，请先跑 strip_sfx.py"

def rep(old, new, tag, expect=1):
    global src
    assert src.count(old) == expect, f"{tag}: anchor x{src.count(old)} (expect {expect})"
    src = src.replace(old, new)

# 1) 文档注释（head 前）
DOC = """<html lang="zh-CN">
<!--
  ═════════════════════════════════════════════════════════════════
  开屏特效 · 通用模板（主轨劈开 → 辅轨展开 → 三环光圈水波涟漪晕开 → 全屏清晰）
  ─────────────────────────────────────────────────────────────────
  ▍换背景图   改脚本里 CONFIG.bgImage（文件 / URL / dataURI 均可），
              或把你的图命名为 bg.jpg 放在本文件同目录（建议 ≥1920 宽横图）
  ▍做视频开头 浏览器打开本文件 → F11 全屏 → 录屏即可；要离线单文件
              就运行 build_universal.py 打包（背景图 base64 内联）
  ▍加到网页   ① 把 <main id="site">…</main> 整块换成你自己的页面内容；
              ② 或在任意网页嵌入：
              <iframe src="开屏特效_通用模板.html" style="position:fixed;inset:0;width:100%;height:100%;border:0;z-index:99999"></iframe>
  ▍品牌文案   直接改 HTML 里 <div class="brand"> 与 <main id="site"> 的演示文字
  ▍时间轴     speed=0.8：0.24s 主轨劈开 → 1.01s 涟漪小点 → 2.05s 辅轨满屏
              → 2.36s 光圈收满全清晰 → 2.76s 品牌定格 → ≈3.7s 收尾完毕
  ═════════════════════════════════════════════════════════════════
-->
<head>"""
rep('<html lang="zh-CN">\n<head>', DOC, "doc")

# 2) CSS 变量默认背景
rep("  :root { color-scheme: dark; }",
    "  :root { color-scheme: dark; --bg: url('bg.jpg'); }   /* 默认背景图，JS 会用 CONFIG.bgImage 覆盖 */", "root-var")

# 3) 7 处 CSS __BG__ → var(--bg)（第 8 处是 img src，由步骤 4 处理）
rep('url("__BG__")', "var(--bg)", "bg-var", expect=7)
assert 'url("__BG__")' not in src

# 4) scene img 去 src（JS 注入）
rep('<div class="scene"><img id="sceneImg" src="__BG__" alt=""></div>',
    '<div class="scene"><img id="sceneImg" alt=""></div>', "scene-img")

# 5) 标题
rep("<title>开屏动效 · 刀刃 × 瞳孔转场</title>", "<title>开屏特效 · 通用模板</title>", "title")

# 6) CONFIG 配置区（IIFE 开头）
rep("(function () {",
    """(function () {
  /* ═══ 配置区：改这里即可换背景图 / 速度 ═══ */
  var CONFIG = {
    bgImage: 'bg.jpg',      /* 背景图：同目录文件 / 相对路径 / 网络URL / dataURI 均可 */
    speed:   0.8,           /* 全局速度：<1 加速、>1 放慢（0.8 ≈ 整场 3 秒级） */
    showSkip: true          /* 「跳过」按钮；点击画面任意处始终可跳过 */
  };
  var BG_URL = CONFIG.bgImage;
  document.documentElement.style.setProperty('--bg', 'url("' + BG_URL + '")');""", "config")

# 7) SPEED 接 CONFIG
rep("  var SPEED = 0.8;   /* 全局速度：<1 加速（0.8=提速 20%）。时间轴唯一缩放入口，所有相位等比压缩 */",
    "  var SPEED = CONFIG.speed;   /* 全局速度：唯一缩放入口，所有相位等比压缩 */", "speed-cfg")

# 8) 资源注入 + 跳过开关
rep("  var sceneImg = document.getElementById('sceneImg');",
    """  var sceneImg = document.getElementById('sceneImg');
  sceneImg.src = BG_URL;
  if (!CONFIG.showSkip) skipBtn.style.display = 'none';""", "wiring")

for need in ["CONFIG.bgImage", "CONFIG.speed", "CONFIG.showSkip",
             "var(--bg)", "setProperty('--bg'"]:
    assert need in src, f"缺失: {need}"
assert src.count("bgImage: 'bg.jpg'") == 1
assert "sfx" not in src and "__BG__" not in src

DST.write_text(src, encoding="utf-8")
print("UNIVERSAL OK  bytes:", n0, "->", len(src), "->", DST)
