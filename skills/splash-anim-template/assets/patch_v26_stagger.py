# -*- coding: utf-8 -*-
"""v26 三环错峰改造：splash_template.html（v25 源）原子补丁
① rm 常数比例 → ms 张开式（外-次间距全程单调增，次外圈 1.56 淡入出场）
② kk 窗口 1.30/1.05·0.46-0.43 → 1.74/1.21·0.50-0.42（外-内峰值拉大、终距 0.08r、≈2.69 反超次外）
③ 淡入 oI/oM/oC 错峰 1.26/1.56/1.86
注释块同步改写。断言式原子替换，跑完 grep 校验零旧痕迹。
"""
import os, pathlib, tempfile

SRC = pathlib.Path(os.environ["WORKSPACE"]) / ".workbuddy/splash_template.html"
src = SRC.read_text(encoding="utf-8")
n0 = len(src)

def rep(old, new, tag, expect=1):
    global src
    n = src.count(old)
    assert n == expect, f"{tag}: x{n} (expect {expect})"
    src = src.replace(old, new)

# ① 注释块改写
OLD_DOC = """    /* --- 光圈三环（水波涟漪 v24）：1.26s 自主轨中心一个很小的点晕开，如石子入水渐起圈纹 ---
       单一半径曲线 r = R·inOutQuad((t-1.26)/1.69)：起止速度均为 0 → 慢起步（1.30s≈2px）且收尾缓停，
       全片速度连续（旧版入场 ramp 与 slack 二段加速两个停顿感来源已删除）；三环同曲线异比例：
       最外圈 r、次外圈 rm=0.87r（外-次间距 0.13r 随 r 单调增大）、内圈 rc=r(1-k)，
       k 自 0.46 → 0.03 单调收窄（smoothstep 1.30→2.35s）：内圈起初落后（0.54r 清晰小点），
       ≈2.02s 追平次外圈转亮带（比原背景稍亮、随涟漪渐宽），全程 rc ≤ r 不超最外圈；
       越界部分仍被裁剪容器裁掉，2.56s 辅轨满屏后依次扫出全屏（2.95s 收满出屏） */"""
NEW_DOC = """    /* --- 光圈三环（水波涟漪 v26 错峰版）：1.26s 自主轨中心晕开，三环依次错峰启动 ---
       单一半径曲线 r = R·inOutQuad((t-1.26)/1.69) 不变（起止速度均为 0，全片速度连续）；
       三环全部由主曲线派生 + 错峰淡入：最外圈 1.26s 起常显；次外圈 rm=r(1-0.13·ms)，
       ms=ss((t-1.56)/0.35)——半径随 r 同步生长但 1.56s 才淡入（出生贴外圈内缘、随 ms 单调
       拉开，外-次间距 0.13·ms·r 全程单调增）；内圈 rc=r(1-kk)，kk=0.50-0.42·ss((t-1.74)/1.21)
       ——外-内间距先增后减（峰值≈0.21r@2.30s）且恒正不交叉；kk 于 ≈2.69s 穿过 0.13：
       内圈反超次外圈一次（亮带经 min(rc,rm) 连续切换），终态三环 1:0.87:0.92；
       错峰淡入 oI/oM/oC = 1.26/1.56/1.86（间隔 0.30 相位 = 0.24s 实钟，落在 0.2-0.4s 区间）；
       越界部分仍被裁剪容器裁掉，2.56s 辅轨满屏后依次扫出全屏（2.95s 收满出屏） */"""
rep(OLD_DOC, NEW_DOC, "doc-block")

# ② rm 张开式
OLD_RM = """      rm = 0.87 * r;                         /* 次外圈：0.87 倍速，外-次间距 0.13r 单调增大 */"""
NEW_RM = """      var ms = clamp01((t - 1.56) / 0.35); ms = ms * ms * (3 - 2 * ms);
      rm = r * (1 - 0.13 * ms);              /* 次外圈：出生贴外圈内缘，0.35s 张开至 0.87r；外-次间距全程单调增 */"""
rep(OLD_RM, NEW_RM, "rm-formula")

# ③ kk 窗口与终值
OLD_KK = """      var ks = clamp01((t - 1.30) / 1.05); ks = ks * ks * (3 - 2 * ks);
      var kk = 0.46 - 0.43 * ks;             /* 内圈落后比 0.46→0.03：先落后、后追赶、≈2.02s 追平 */
      rc = r * (1 - kk);                     /* 内圈：清晰小点与涟漪同生（1.26s 起），追平后转亮带 */"""
NEW_KK = """      var ks = clamp01((t - 1.74) / 1.21); ks = ks * ks * (3 - 2 * ks);
      var kk = 0.50 - 0.42 * ks;             /* 内圈落后比 0.50→0.08：深居内缓追，≈2.69s 反超次外圈，终距最外 0.08r */
      rc = r * (1 - kk);                     /* 内圈：清晰小点随 rc 从 0 长出（1.86s 起显示），反超后转亮带 */"""
rep(OLD_KK, NEW_KK, "kk-window")

# ④ 错峰淡入
OLD_O = """      var oI = clamp01((t - 1.26) / 0.08), oM = clamp01((t - 1.27) / 0.10), oC = clamp01((t - 1.27) / 0.14);   /* 涟漪小点：三环自点同生、几乎同时淡入（内核随 rc 从 0 长出） */"""
NEW_O = """      var oI = clamp01((t - 1.26) / 0.10), oM = clamp01((t - 1.56) / 0.12), oC = clamp01((t - 1.86) / 0.12);   /* 错峰淡入：外 1.26 → 次 1.56 → 内 1.86（间隔 0.30 相位 = 0.24s 实钟） */"""
rep(OLD_O, NEW_O, "fade-stagger")

# 终检：新 token 在、旧 token 清零
for need in ["0.13 * ms", "1.74) / 1.21", "0.50 - 0.42", "(t - 1.86) / 0.12", "v26 错峰版"]:
    assert need in src, f"缺失: {need}"
for bad in ["0.87 * r", "1.30) / 1.05", "0.46 - 0.43", "(t - 1.27) / 0.10", "≈2.02s 追平", "水波涟漪 v24"]:
    assert bad not in src, f"残留: {bad}"

fd, tmp = tempfile.mkstemp(dir=str(SRC.parent), suffix=".tmp")
with os.fdopen(fd, "w", encoding="utf-8", newline="") as f:
    f.write(src)
os.replace(tmp, SRC)
print(f"V26 PATCH OK {n0} -> {len(src)} bytes -> {SRC}")
