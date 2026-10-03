# -*- coding: utf-8 -*-
"""splash 构建模板 → 最终单文件（base64 注入 bg_clean.jpg / whoosh.mp3）"""
import os
import base64, pathlib

ROOT = pathlib.Path(os.environ["WORKSPACE"])
tpl = (ROOT / ".workbuddy/splash_template.html").read_text(encoding="utf-8")
bg  = base64.b64encode((ROOT / ".workbuddy/bg_clean.jpg").read_bytes()).decode()
sfx = base64.b64encode((ROOT / ".workbuddy/whoosh.mp3").read_bytes()).decode()

n_bg = tpl.count("__BG__")
assert n_bg == 8, f"__BG__ count {n_bg} != 7"  # scene1+aux1+iris/mid/core各1+slit1+slitPad1
assert tpl.count("__SFX__") == 1
out = tpl.replace("__BG__", "data:image/jpeg;base64," + bg) \
         .replace("__SFX__", "data:audio/mpeg;base64," + sfx)
dest = ROOT / "开屏动效_刀刃瞳孔转场.html"
dest.write_text(out, encoding="utf-8")
print("BUILD OK ->", dest, f"{dest.stat().st_size/1024:.0f} KB")
