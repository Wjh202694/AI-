# -*- coding: utf-8 -*-
"""通用模板打包器：把 CONFIG.bgImage 指向的背景图 base64 内联 → 离线单文件
2.2.0：无音效版（不再内联音频）。
用法: python build_universal.py [背景图] [输出文件]   （参数可省略用默认演示资源）
"""
import os
import base64, pathlib, sys

ROOT = pathlib.Path(os.environ["WORKSPACE"])
tpl_path = ROOT / "开屏特效_通用模板.html"
bg_file  = sys.argv[1] if len(sys.argv) > 1 else str(ROOT / ".workbuddy/bg_hd.jpg")
out_file = sys.argv[2] if len(sys.argv) > 2 else str(ROOT / "开屏特效_通用模板_单文件版.html")

html = tpl_path.read_text(encoding="utf-8")

A_BG = "bgImage: 'bg.jpg'"
assert html.count(A_BG) == 1, "CONFIG 锚点缺失：请确认模板未被手改"
assert "sfx" not in html, "模板仍含音效引用，请先跑 strip_sfx.py / patch_universal.py"

def data_uri(p, mime):
    return "data:%s;base64,%s" % (mime, base64.b64encode(pathlib.Path(p).read_bytes()).decode())

html = html.replace(A_BG, "bgImage: '" + data_uri(bg_file, "image/jpeg") + "'")

dest = pathlib.Path(out_file)
dest.write_text(html, encoding="utf-8")
print("PACK OK ->", dest, f"{dest.stat().st_size/1024:.0f} KB")
