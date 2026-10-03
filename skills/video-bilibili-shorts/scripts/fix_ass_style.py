#!/usr/bin/env python3
"""修正 ffmpeg srt->ass 产物，使其满足 B站烧录规格。

ffmpeg 由 srt 转 ass 时会写入 384x288 的虚拟画布（PlayResX/PlayResY），
且 Style 行是小字号、小边距的默认值。libass 按 PlayRes 与实际视频的
比例放大渲染，导致字幕巨幅错位（实测：64px 字号被放大到约 240px、
MarginV 185 把字幕顶到画面上部 1/3 处、左右被裁切）。因此必须同时改写：

  1. PlayResX / PlayResY → 实际视频分辨率（默认 1920x1080）
  2. Style 行的 Fontname / Fontsize / MarginV → 合规值
     （字号 >= 画面高度 1/20；下边距 >= 底部 15% 安全区）

用法:
    python fix_ass_style.py <in.ass> <out.ass> \
        [--font "Microsoft YaHei"] [--size 64] [--marginv 185] \
        [--playres-x 1920] [--playres-y 1080]

字段顺序（ASS Style，共 23 列，索引从 0 起）:
    0 Name, 1 Fontname, 2 Fontsize, ... 18 Alignment, 19 MarginL, 20 MarginR, 21 MarginV, 22 Encoding
"""
import argparse
import sys


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("input")
    ap.add_argument("output")
    ap.add_argument("--font", default="Microsoft YaHei")
    ap.add_argument("--size", type=int, default=64, help="字号，1080p 建议 54-72")
    ap.add_argument("--marginv", type=int, default=185, help="下边距 px，1080p 需 >=162（底部 15%）")
    ap.add_argument("--playres-x", type=int, default=1920)
    ap.add_argument("--playres-y", type=int, default=1080)
    a = ap.parse_args()

    out_lines = []
    style_fixed = False
    playres_fixed = False
    with open(a.input, encoding="utf-8-sig") as f:
        for line in f:
            if line.startswith("PlayResX:"):
                line = f"PlayResX: {a.playres_x}\n"
                playres_fixed = True
            elif line.startswith("PlayResY:"):
                line = f"PlayResY: {a.playres_y}\n"
                playres_fixed = True
            elif line.startswith("Style:") and not style_fixed:
                parts = line[len("Style:"):].strip().split(",")
                if len(parts) >= 23:
                    parts[1] = a.font
                    parts[2] = str(a.size)
                    parts[21] = str(a.marginv)
                    line = "Style: " + ",".join(parts) + "\n"
                    style_fixed = True
                else:
                    print(f"WARN: Style 行字段数异常（{len(parts)} 列），未修正", file=sys.stderr)
            out_lines.append(line)

    if not playres_fixed:
        print("WARN: 未找到 PlayResX/PlayResY（手写 ass？），未改写画布", file=sys.stderr)
    if not style_fixed:
        print("WARN: 未找到可修正的 Style 行", file=sys.stderr)

    with open(a.output, "w", encoding="utf-8", newline="\n") as f:
        f.writelines(out_lines)
    print(f"OK: {a.output}  PlayRes={a.playres_x}x{a.playres_y}  font={a.font}  "
          f"Fontsize={a.size}  MarginV={a.marginv}")


if __name__ == "__main__":
    main()
