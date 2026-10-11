# -*- coding: utf-8 -*-
"""v23c -> v24 水波涟漪模型补丁（锚点切片替换 + 断言 + 自校验）
三处改动：
  A. 光圈三环注释块 + irisRCurve + 状态计算（单一 inOutQuad 涟漪曲线，删 slack/入场 ramp）
  B. opacity 三环淡入时序（三环自小点同生）
  C. 演示页 desc 文案（涟漪叙事）
"""
import os
import pathlib, shutil, sys

P = pathlib.Path(os.environ["WORKSPACE"]) / ".workbuddy/splash_template.html"
bak = P.with_suffix(".html.v23c.bak")
if not bak.exists():
    shutil.copy2(P, bak)
src = P.read_text(encoding="utf-8")
orig = src

# ---------- A. 光圈三环块：切片替换（起点注释 -> "if (r > 0) {" 之前） ----------
A_START = "    /* --- 光圈三环"
A_END = "    if (r > 0) {"
assert src.count(A_START) == 1, f"A_START x{src.count(A_START)}"
assert src.count(A_END) == 1, f"A_END x{src.count(A_END)}"
i0, i1 = src.index(A_START), src.index(A_END)

new_A = """    /* --- 光圈三环（水波涟漪 v24）：1.26s 自主轨中心一个很小的点晕开，如石子入水渐起圈纹 ---
       单一半径曲线 r = R·inOutQuad((t-1.26)/1.69)：起止速度均为 0 → 慢起步（1.30s≈2px）且收尾缓停，
       全片速度连续（旧版入场 ramp 与 slack 二段加速两个停顿感来源已删除）；三环同曲线异比例：
       最外圈 r、次外圈 rm=0.87r（外-次间距 0.13r 随 r 单调增大）、内圈 rc=r(1-k)，
       k 自 0.46 → 0.03 单调收窄（smoothstep 1.30→2.35s）：内圈起初落后（0.54r 清晰小点），
       ≈2.02s 追平次外圈转亮带（比原背景稍亮、随涟漪渐宽），全程 rc ≤ r 不超最外圈；
       越界部分仍被裁剪容器裁掉，2.56s 辅轨满屏后依次扫出全屏（2.95s 收满出屏） */
    function irisRCurve(tt) {
      if (tt < 1.26) return 0;
      var uu = clamp01((tt - 1.26) / 1.69);
      var ee = uu < 0.5 ? 2 * uu * uu : 1 - 2 * (1 - uu) * (1 - uu);   /* inOutQuad：起止速度均为 0 */
      return maxR * 1.08 * ee;   /* R = maxR×1.08：2.95s 收满时半径超出对角线+余量，全出屏 */
    }
    var r = 0, rm = 0, rc = 0, sh = 0;
    if (t >= 1.26) {
      r  = irisRCurve(t);                    /* 最外圈：单一涟漪曲线（慢起步→加速→缓收） */
      rm = 0.87 * r;                         /* 次外圈：0.87 倍速，外-次间距 0.13r 单调增大 */
      var ks = clamp01((t - 1.30) / 1.05); ks = ks * ks * (3 - 2 * ks);
      var kk = 0.46 - 0.43 * ks;             /* 内圈落后比 0.46→0.03：先落后、后追赶、≈2.02s 追平 */
      rc = r * (1 - kk);                     /* 内圈：清晰小点与涟漪同生（1.26s 起），追平后转亮带 */
      sh = clamp01((rm - rc) / 26);          /* 阴影：随 r·(k-0.13) 先涨后消（峰值≈0.73），重合即彻底消失 */
    }
"""
src = src[:i0] + new_A + src[i1:]

# ---------- B. opacity 时序 ----------
B_OLD = "var oI = clamp01((t - 1.26) / 0.08), oM = clamp01((t - 1.38) / 0.12), oC = clamp01((t - 1.50) / 0.15);   /* 外环快显（参照帧1 小球清晰）；中/内核依次 */"
B_NEW = "var oI = clamp01((t - 1.26) / 0.08), oM = clamp01((t - 1.27) / 0.10), oC = clamp01((t - 1.27) / 0.14);   /* 涟漪小点：三环自点同生、几乎同时淡入（内核随 rc 从 0 长出） */"
assert src.count(B_OLD) == 1, f"B_OLD x{src.count(B_OLD)}"
src = src.replace(B_OLD, B_NEW)

# ---------- C. desc 文案 ----------
C_START = "光圈与辅轨同步（1.26s）自主轨中心依次晕开"
C_END = "各环以独立亮缘分界（圈缘分明）；"
assert src.count(C_START) == 1, f"C_START x{src.count(C_START)}"
assert src.count(C_END) == 1, f"C_END x{src.count(C_END)}"
j0 = src.index(C_START)
j1 = src.index(C_END) + len(C_END)
new_C = (
    "光圈与辅轨同步（1.26s）自主轨中心一个很小的点晕开——如石子入水、涟漪渐起：单一 inOutQuad 半径曲线"
    "起止速度均为 0，慢起步、缓收尾，全片速度连续无停顿；三环自小点同生：最外圈最速、次外圈 0.87 倍速"
    "（外-次间距随半径单调增大）、内圈起初落后（约 0.54r 的清晰小点）后加速追赶，≈2.0s 追平次外圈——"
    "轻模糊淡阴影渐消、转为比原背景稍亮的清晰亮带并随涟漪渐宽，内圈全程不超最外圈，越界部分被裁剪容器裁掉，"
    "2.56s 辅轨满屏后三环依次扫出全屏（2.95s 收满出屏），圈外灰白模糊，各环以独立亮缘分界（圈缘分明）；"
)
src = src[:j0] + new_C + src[j1:]

# ---------- 断言：旧痕迹清零 ----------
for bad in ["var slack", "(maxR * 1.14", "irisRCurve(1.48)", "clamp01((tt - 2.00)", "clamp01((t - 1.38)", "clamp01((t - 1.50) / 0.15)",
            "贴轨小球", "紧贴已展开轨缘", "贴轨前沿", "与辅轨 e 曲线严格一致", "入场 0.12s", "自主轨中心依次晕开"]:
    assert bad not in src, f"旧痕迹残留: {bad}"
for need in ["1.69", "0.46 - 0.43 * ks", "maxR * 1.08 * ee", "0.54r 清晰小点",
             "一个很小的点晕开", "石子入水"]:
    assert need in src, f"新内容缺失: {need}"
assert src.count("irisRCurve") == 2, f"irisRCurve x{src.count('irisRCurve')} (定义+1次调用)"
assert src.count("if (r > 0) {") == 1

P.write_text(src, encoding="utf-8")
print("PATCH OK  bytes:", len(orig), "->", len(src))
print("backup:", bak)
