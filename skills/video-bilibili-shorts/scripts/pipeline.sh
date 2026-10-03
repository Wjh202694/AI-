#!/usr/bin/env bash
# B站短视频合成管线（2026-09-20 全链实测通过：Windows/Git Bash + ffmpeg 9.0.1 + Python 3.12）
# 链路：分段标准化 → concat → srt转ass+样式修正(PlayRes/字体/字号/安全区) → 烧录 + BGM(-14 LUFS, -shortest)
#
# 用法:
#   bash pipeline.sh <素材目录> <字幕.srt> <BGM音频> <输出.mp4> [宽 高 帧率]
# 示例:
#   bash pipeline.sh segs/ sub.zh.srt bgm.mp3 final.mp4 1920 1080 30
# 说明:
#   - 素材目录内按文件名排序的 *.mp4 视为分段（建议 seg01/seg02... 命名；分辨率/帧率可不一致，管线统一标准化）
#   - 字幕为中文字幕轨（.srt）；BGM 响度归一到 -14 LUFS；输出 MP4/H.264/AAC
set -euo pipefail

SEG_DIR="${1:?用法: pipeline.sh <素材目录> <字幕.srt> <BGM> <输出.mp4> [宽 高 帧率]}"
SUB_SRT="${2:?缺少字幕 .srt}"
BGM="${3:?缺少 BGM 音频}"
OUT="${4:?缺少输出路径}"
W="${5:-1920}"; H="${6:-1080}"; FPS="${7:-30}"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# 全部转为绝对路径（后面会 cd 进工作目录，ass 滤镜用相对路径规避盘符冒号/空格转义坑）
abs() { local p="$1"; python -c "import os,sys; print(os.path.abspath(sys.argv[1]))" "$p"; }
SEG_DIR="$(abs "$SEG_DIR")"; SUB_SRT="$(abs "$SUB_SRT")"; BGM="$(abs "$BGM")"; OUT="$(abs "$OUT")"

# 按安全区规格等比计算字号与下边距（基准 1080p: 64px / 185px；同时兜底规格下限）
FONT_SIZE=$(( H * 64 / 1080 )); [ "$FONT_SIZE" -lt $(( H / 20 )) ] && FONT_SIZE=$(( H / 20 ))
MARGIN_V=$(( H * 185 / 1080 )); [ "$MARGIN_V" -lt $(( H * 15 / 100 )) ] && MARGIN_V=$(( H * 15 / 100 ))

WORK="$SEG_DIR/_pipeline_tmp"; mkdir -p "$WORK"

echo "[1/5] 标准化分段 → ${W}x${H}@${FPS}"
i=0
shopt -s nullglob
for f in "$SEG_DIR"/*.mp4; do
  i=$((i+1))
  ffmpeg -hide_banner -loglevel error -y -i "$f" \
    -vf "scale=${W}:${H}:force_original_aspect_ratio=decrease,pad=${W}:${H}:(ow-iw)/2:(oh-ih)/2,setsar=1" \
    -r "$FPS" -c:v libx264 -pix_fmt yuv420p -an "$WORK/seg_$(printf '%03d' $i).mp4"
done
[ "$i" -eq 0 ] && { echo "错误：素材目录（$SEG_DIR）内没有 mp4"; exit 1; }
echo "  共 $i 个分段"

echo "[2/5] 拼接"
: > "$WORK/list.txt"
for f in "$WORK"/seg_*.mp4; do echo "file '$f'" >> "$WORK/list.txt"; done
ffmpeg -hide_banner -loglevel error -y -f concat -safe 0 -i "$WORK/list.txt" -c copy "$WORK/merged.mp4"

echo "[3/5] srt→ass + 样式修正（PlayRes ${W}x${H}，字号 ${FONT_SIZE}px，下边距 ${MARGIN_V}px）"
ffmpeg -hide_banner -loglevel error -y -i "$SUB_SRT" "$WORK/sub.ass"
python "$SCRIPT_DIR/fix_ass_style.py" "$WORK/sub.ass" "$WORK/sub.fixed.ass" \
  --font "Microsoft YaHei" --size "$FONT_SIZE" --marginv "$MARGIN_V" --playres-x "$W" --playres-y "$H"

echo "[4/5] 烧录字幕 + BGM 响度归一（-14 LUFS，-shortest）"
# cd 进工作目录后用相对路径喂 ass 滤镜（实测最稳，规避 Windows 盘符冒号/空格转义）
( cd "$WORK" && ffmpeg -hide_banner -loglevel error -y -i merged.mp4 -i "$BGM" \
  -filter_complex "[0:v]ass=sub.fixed.ass[v];[1:a]loudnorm=I=-14:TP=-1.5:LRA=11[bgm]" \
  -map "[v]" -map "[bgm]" -c:v libx264 -pix_fmt yuv420p -ar 48000 -ac 2 -shortest "$OUT" )

echo "[5/5] 校验"
ffprobe -v error -show_entries stream=codec_type,codec_name,width,height,r_frame_rate -of csv=p=0 "$OUT"
echo "时长: $(ffprobe -v error -show_entries format=duration -of csv=p=0 "$OUT")s"
echo "输出: $OUT"
echo "提示：抽帧目检字幕 —— ffmpeg -ss <秒> -i \"$OUT\" -frames:v 1 check.png"
