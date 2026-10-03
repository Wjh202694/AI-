# -*- coding: utf-8 -*-
"""v23: 三环差速 + 中带淡阴影/重合转亮带。
- 次外圈 rm=0.87·F 最慢；最外圈 r=F 居中；内圈 rc=F-gap 最快（gap 1.5→2.35s 渐窄）
- 内圈未追平次外圈：[rc,rm] 轻模糊+淡阴影（brightness 随重合渐隐，重合即消失）
- 内圈超越后：[rm,rc] 无模糊无阴影亮带（brightness 1.12，新层 core-bright）
- 内圈与最外圈之间恒为重模糊；rc<r 全程成立"""
import os
import pathlib

P = pathlib.Path(os.environ["WORKSPACE"]) / ".workbuddy/splash_template.html"
s = P.read_text(encoding="utf-8")

def rep(old, new, tag, cnt=1):
    global s
    c = s.count(old)
    assert c == cnt, f"[{tag}] count={c} (expect {cnt})"
    s = s.replace(old, new)
    print(f"ok {tag}")

# 1) CSS：内圈亮带层
rep("""  /* 光圈三环 · 内圈：清晰实景核心 */
  .core {
    position: absolute; left: 50%; top: 50%; z-index: 4;
    width: 0; height: 0; border-radius: 50%;
    transform: translate(-50%, -50%);
    background: url("__BG__") no-repeat;
  }
""",
"""  /* 光圈三环 · 内圈：清晰实景核心 */
  .core {
    position: absolute; left: 50%; top: 50%; z-index: 4;
    width: 0; height: 0; border-radius: 50%;
    transform: translate(-50%, -50%);
    background: url("__BG__") no-repeat;
  }

  /* 光圈三环 · 内圈亮带：内圈超越次外圈后，两圈之间显示比原背景稍亮的清晰实景
     （无阴影无模糊）；内圈未超越时被内圈核心完全覆盖、不可见 */
  .core-bright {
    position: absolute; left: 50%; top: 50%; z-index: 3;
    width: 0; height: 0; border-radius: 50%;
    transform: translate(-50%, -50%);
    background: url("__BG__") no-repeat;
    filter: brightness(1.12);
  }
""", "css-core-bright")

# 2) HTML：三套副本各插入 core-bright（ring 与 core 之间）
for suf in ["L", "S", "R"]:
    rep(f"""      <div class="ring" id="ring{suf}"></div>
      <div class="core" id="core{suf}"></div>""",
        f"""      <div class="ring" id="ring{suf}"></div>
      <div class="core-bright" id="coreBright{suf}"></div>
      <div class="core" id="core{suf}"></div>""", f"html-coreBright{suf}")

# 3) mkSet：注册 coreBright
rep("""    return { iris: document.getElementById('iris' + suf), mid: document.getElementById('mid' + suf), ring: document.getElementById('ring' + suf), core: document.getElementById('core' + suf),""",
"""    return { iris: document.getElementById('iris' + suf), mid: document.getElementById('mid' + suf), ring: document.getElementById('ring' + suf), coreBright: document.getElementById('coreBright' + suf), core: document.getElementById('core' + suf),""",
"mkSet")

# 4) 注释块
rep("""    /* --- 光圈三环：与辅轨同步 1.26s 起自主轨中心依次晕开（参照帧：先中心贴轨小球→再显完整三环）---
       半径 = 辅轨半宽 + slack：光圈缘始终紧贴已展开轨缘，越界部分被裁剪容器裁掉（不超辅轨已展开区域）；
       外环→中环→内核各滞后 0.12/0.24s 依次浮现；1.75s 起 slack 加速，
       2.56s 辅轨满屏后三环依次超出界面，全屏转清晰 */""",
"""    /* --- 光圈三环（差速）：最外圈贴轨前沿（速度居中）、次外圈 0.87 倍速最慢、内圈最快（前沿速+间距收缩追赶）---
       内圈未追平次外圈：两圈之间=轻模糊+淡阴影（brightness 随重合度渐隐，重合即彻底消失）；
       内圈超越后：两圈之间=无模糊无阴影的亮带（brightness 1.12 比原背景稍亮，由内圈亮带层显示），
       内圈与最外圈之间恒为重模糊；内圈-最外圈间距 1.5→2.35s 渐窄，全程内圈不超最外圈；
       半径始终紧贴已展开轨缘，越界部分被裁剪容器裁掉；2.56s 辅轨满屏后依次扫出全屏 */""",
"comment")

# 5) 半径计算：差速 + 阴影强度
rep("""    var r = 0, rm = 0, rc = 0;
    if (t >= 1.26) {
      r  = irisRCurve(t);
      rm = irisRCurve(t - 0.12);
      rc = irisRCurve(t - 0.24);
    }""",
"""    var r = 0, rm = 0, rc = 0, sh = 0;
    if (t >= 1.26) {
      r  = irisRCurve(t);                    /* 最外圈：贴轨前沿，速度居中 */
      rm = 0.87 * r;                         /* 次外圈：最慢（0.87 倍速），与最外圈间距收窄 */
      var g0 = irisRCurve(1.48);             /* 内圈-最外圈初始间距 */
      var su = clamp01((t - 1.50) / 0.85); su = su * su * (3 - 2 * su);
      var gap = g0 * (1 - 0.75 * su);        /* 间距 1.5→2.35s 渐窄至 0.25·g0，内圈恒不超最外圈 */
      rc = Math.max(0, r - gap);             /* 内圈：最快（前沿速+间距收缩追赶） */
      sh = clamp01((rm - rc) / 36);          /* 阴影：未追平时渐显，重合即彻底消失 */
    }""",
"radii")

# 6) 透明度块：mid 动态阴影滤镜 + coreBright 透明度
rep("""      irisSets.forEach(function (s) {
        s.iris.style.opacity = oI.toFixed(3);
        s.mid.style.opacity = oM.toFixed(3);
        s.core.style.opacity = oC.toFixed(3);""",
"""      irisSets.forEach(function (s) {
        s.iris.style.opacity = oI.toFixed(3);
        s.mid.style.opacity = oM.toFixed(3);
        s.mid.style.filter = 'blur(3.5px) brightness(' + (1 - 0.14 * sh).toFixed(3) + ')';   /* 淡阴影：随重合渐隐 */
        s.coreBright.style.opacity = oC.toFixed(3);
        s.core.style.opacity = oC.toFixed(3);""",
"opacity-shadow")

# 7) 尺寸：coreBright=rc；core=min(rc,rm)
rep("""        s.core.style.width = (rc * 2).toFixed(1) + 'px';
        s.core.style.height = (rc * 2).toFixed(1) + 'px';
        bgCover(s.core, vw / 2 - rc, vh / 2 - rc, rc * 2, rc * 2);""",
"""        s.coreBright.style.width = (rc * 2).toFixed(1) + 'px';
        s.coreBright.style.height = (rc * 2).toFixed(1) + 'px';
        bgCover(s.coreBright, vw / 2 - rc, vh / 2 - rc, rc * 2, rc * 2);
        var rcIn = Math.min(rc, rm);   /* 内圈核心：未追平时=内圈（盖住亮带），追平后=次外圈（亮带显形） */
        s.core.style.width = (rcIn * 2).toFixed(1) + 'px';
        s.core.style.height = (rcIn * 2).toFixed(1) + 'px';
        bgCover(s.core, vw / 2 - rcIn, vh / 2 - rcIn, rcIn * 2, rcIn * 2);""",
"sizing")

# 8) reset：coreBright + mid 滤镜还原
rep("""      s.core.style.width = '0px'; s.core.style.height = '0px';
      s.iris.style.opacity = '0'; s.mid.style.opacity = '0'; s.core.style.opacity = '0';
      s.ring.style.opacity = '0';""",
"""      s.core.style.width = '0px'; s.core.style.height = '0px';
      s.coreBright.style.width = '0px'; s.coreBright.style.height = '0px';
      s.iris.style.opacity = '0'; s.mid.style.opacity = '0'; s.core.style.opacity = '0';
      s.coreBright.style.opacity = '0';
      s.mid.style.filter = '';
      s.ring.style.opacity = '0';""",
"reset")

# 9) desc 文案
rep("""    半径始终紧贴已展开轨缘（越界部分被裁掉、不超辅轨已展开区域），2.56s 辅轨满屏后三环依次扫出全屏，呈三环结构：圈外灰白模糊、外环原色重模糊、次环轻模糊、内圈清晰，各环以独立亮缘分界（圈缘分明）；""",
"""    半径始终紧贴已展开轨缘（越界部分被裁掉、不超辅轨已展开区域），2.56s 辅轨满屏后三环依次扫出全屏；三环差速晕开（次外圈最慢、内圈最快、最外圈居中）：内圈未追平次外圈时两圈之间为轻模糊+淡阴影，
    重合瞬间阴影彻底消失、转为比原背景稍亮的清晰亮带，内圈与最外圈之间保持重模糊且间距渐窄（内圈全程不超最外圈），圈外灰白模糊，各环以独立亮缘分界（圈缘分明）；""",
"desc")

P.write_text(s, encoding="utf-8")
print("patched OK")

# 构建脚本断言 7 -> 8（.core-bright CSS 新增 1 处 __BG__）
B = pathlib.Path(os.environ["WORKSPACE"]) / ".workbuddy/build_splash.py"
b = B.read_text(encoding="utf-8")
old_a = "assert n_bg == 7"
if old_a in b:
    b = b.replace(old_a, "assert n_bg == 8")
    B.write_text(b, encoding="utf-8")
    print("build assert 7 -> 8")
else:
    print("WARN: assert pattern not found, check build_splash.py")
