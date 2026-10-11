---
name: video-bilibili-shorts
version: 1.1.0
display_name: B站短视频制作
description: 社媒短视频（侧重B站）制作流水线。将文案/主题转为带中英双语字幕、风格贴合的短视频，输出无配音成片与真人配音文案。适用于B站投稿、知识科普、产品演示、品牌短片。触发词：B站视频、短视频制作、中英字幕、无配音成片、真人配音文案、视频投稿。
read_when:
  - 制作发布到B站的短视频
  - 需要中英双语字幕且字幕贴合内容风格
  - 同时需要无配音视频与真人配音文案
  - 用户提到 bilibili / B站 / 短视频投稿
---

# 社媒短视频制作（B站向）

## 功能定位
面向 B站等社媒的短视频生产流水线：主题/文案 → 分镜与画面提示词 → 素材生成 → 剪辑合成 → 成片。
输出端分两条线：① 无配音成片（字幕烧录或独立字幕轨，配 BGM/音效）；② 真人配音文案（供真人/配音员录制）。

## 何时使用
- B站投稿的口播、知识科普、产品演示、品牌短片
- 需要中英双语字幕，且字幕语气需贴合视频风格（搞笑/硬核/古风/带货等）
- 既要「无配音版」又要有「真人配音该念的文案」

## 工作流（可执行层）
1. 定位确认：平台=B站、时长、画风、受众语气。
2. 分镜+文案：
   - 用附录 A「时长-字数公式」估算每镜文案量，逐镜校验「镜头时长 × 语速 ≥ 该镜字数」。
   - 每镜给出画面提示词 + 文案段落 + 情感/语速标记。
3. 素材生成：调用 h3-prompt-writing 的 T2VA / I2VA 提示词结构（按其 references 模式组织），再由 VideoGen / ImageGen 工具产出。
4. 字幕：中文为主、英文为辅，风格贴合（见关键规则）。优先产出**中/英两条独立外挂字幕轨**（B站支持观众切换）；如需烧录用 .ass。
   - 已有音视频时，可调用 local-whisper skill 做听写 + 时间轴对齐，导出 .srt 再转 .ass。
5. 合成：优先 `bash scripts/pipeline.sh <素材目录> <字幕.srt> <BGM> <输出.mp4>`（2026-09-20 实测；内含标准化→拼接→srt转ass+样式修正→烧录+BGM）；或按附录 A 手写命令。
6. 封面：本地无图生图时，走「HTML 排版 → agent-browser 截图」（文字可控、风格一致），尺寸见附录 A「B站投稿规格」。
7. 交付前 QC：跑附录 A「交付前 QC 清单」（每项附检查方法）。

## 输入
- 主题或完整脚本（中文优先）
- 平台=B站、时长、分辨率、画风、受众语气
- 参考素材/竞品链接（可选）
- 配音风格要求（角色情感、语速，可选）

## 输出
- 无配音成片 mp4（含中英字幕 + BGM/音效轨）
- 独立字幕文件 .srt/.ass（中 + 英，可切换）
- 真人配音文案 .md：分段文案 + 时间轴 + 情绪/重音标记
- 分镜脚本 .md（每镜画面提示词 + 文案 + 风格标注）
- 封面图（HTML 排版 → agent-browser 截图）

## 关键规则
- 字幕风格贴合：搞笑类轻松口语化中英对照；硬核科普准确术语；古风文雅措辞；带货强节奏短句。中文为正、英文次之，禁机翻腔。
- 全片中文规范：禁英文闲杂词；片尾署名原 "AI" 改「人工智能」。
- 双语字幕须与画面/口播时间轴对齐，避免溢框；优先中/英双外挂轨。
- 无配音版 ≠ 静音：至少加版权安全 BGM/音效轨并响度归一，否则观感像「视频坏了」。
- 「无配音成片」与「真人配音文案」内容一致，仅呈现形态不同。
- **ass 必须修 PlayRes**（实测）：ffmpeg 的 srt→ass 产物带 384×288 虚拟画布，libass 按比例放大渲染，字幕错位到画面上部、字号超标、左右裁切；`scripts/fix_ass_style.py` 同时改 PlayResX/Y 与 Style 行，缺一不可。
- **BGM 必须带 -shortest**（实测）：BGM 比画面长（常态）时，不带 -shortest 成片被音频拖长；无音轨视频禁用 amix（报 matches no streams），用 BGM 单轨 loudnorm。

## 环境依赖 + 降级
- 依赖：h3-prompt-writing（提示词结构）、VideoGen/ImageGen（素材）、ffmpeg（合成）、agent-browser（封面截图）、可选 local-whisper（字幕对齐）。
- 降级：
  - 无 VideoGen/ImageGen → 仅交付分镜脚本 + 真人配音文案 + 字幕文件 + ffmpeg 配方，标注「素材待补」。
  - 无 ffmpeg → 交付分段素材 + 配方清单，提示用户本地执行合成。
  - 无 local-whisper → 字幕时间轴改手工对齐，标注未自动同步。

## 验收标准
- QC 清单全过（每项按附录 A 标注的方法检查）：字幕无溢框/错别字、中英时间轴对齐、A/V 同步、编码合规（MP4/H.264/AAC）。
- 时长-字数校验：每镜字数 ≤ 镜头时长 × 语速上限。
- 无配音版含 BGM/音效轨且响度归一；真人配音文案时长与成片匹配。
- 封面尺寸合规、文字可读。

## 协作（给主会话的指令）
- 成品发布 B站建议主会话调用 skill: web-avatar-subagent（网页替身）。
- 封面/品牌视觉可与 skill: ui-award-design（获奖级 UI 设计）互供。

---

## 附录 A：B站短视频规格与实操配方

### 1. 时长-字数公式（防文案超长）
- 中文口播语速：约 **4–5 字/秒**（平静科普偏慢 4，带货/快剪偏快 5）。
- 60 秒文案约 **240–300 字**；逐镜校验：`镜头时长(秒) × 语速 ≥ 该镜字数`。
- 例：8 秒镜 × 4.5 = 36 字上限，超出则拆镜或减字。

### 2. B站投稿规格
- 容器/编码：**MP4 / H.264 / AAC**；分辨率 1920×1080（横）或 1080×1920（竖）；帧率 ≤ 60，建议 30。
- 封面：建议 **≥1146×717（约 16:10）**，最低 960×600，JPG/PNG ≤5MB（2026-09-20 联网查证：多来源一致、官方原文未达，置信度中高）；16:9 图亦可上传，竖屏可用 1080×1920。文字区居中、留安全边。
- 字幕安全区：烧录字幕避开**底部约 15%**（播放器控件 + 弹幕热区），上沿留 ≥5%；字号 ≥ 画面高度 1/20。

### 3. ffmpeg 端到端管线（顺序：标准化 → 拼接 → 烧字幕+加 BGM）
> Windows / Git Bash 注意：ass 路径盘符冒号需转义 `ass='C\:/path/sub.ass'`；中文字幕需字体存在，否则烧出方块——确认 .ass 的 Style 行 `FontName` 与已安装字体一致（如 `Microsoft YaHei`），或在滤镜补字体目录 `:fontsdir=C\:/Windows/Fonts`。

```bash
# 0) 关键前提：AI 分段常分辨率/帧率/SAR 不一致，先统一转码再 concat，否则花屏/时长错乱
ffmpeg -i seg_raw.mp4 -vf "scale=1920:1080:force_original_aspect_ratio=decrease,pad=1920:1080:(ow-iw)/2:(oh-ih)/2,setsar=1" -r 30 -c:v libx264 -pix_fmt yuv420p -c:a aac seg.mp4

# 1) 拼接（list.txt: file 'seg1.mp4' ...），用转码后一致的分段
ffmpeg -f concat -safe 0 -i list.txt -c copy merged.mp4

# 2) srt -> ass + 样式修正（必须：默认带 PlayRes 384x288 虚拟画布，不改字幕会错位/超标/裁切）
ffmpeg -i sub.zh.srt sub.zh.ass
python scripts/fix_ass_style.py sub.zh.ass sub.fixed.ass --font "Microsoft YaHei" --size 64 --marginv 185

# 3a) 主场景：无配音成片（分段常无音轨）→ BGM 单轨 loudnorm；必须 -shortest（实测：BGM 长于画面时成片被拖长）；勿用 amix（报 matches no streams）
ffmpeg -i merged.mp4 -i bgm.mp3 -filter_complex "[1:a]loudnorm=I=-14:TP=-1.5:LRA=11[bgm]" -map 0:v -map "[bgm]" -c:v copy -ar 48000 -ac 2 -shortest out_silent_bgm.mp4

# 3b) 已加真人/AI 配音版（video 含音轨）→ 才用 amix 混音
ffmpeg -i merged_voice.mp4 -i bgm.mp3 -filter_complex "[1:a]loudnorm=I=-14:TP=-1.5:LRA=11[bgm];[0:a][bgm]amix=inputs=2:duration=first:dropout_transition=0" -map 0:v -map 0:a -c:v copy -ar 48000 -ac 2 out_voice_bgm.mp4

# 4) 烧字幕 + 加 BGM 合并一条（ass 用修正后的 sub.fixed.ass；最稳：cd 到字幕目录用相对文件名，规避盘符冒号/空格转义；-shortest 必须）
ffmpeg -i merged.mp4 -i bgm.mp3 -filter_complex "[0:v]ass=sub.fixed.ass[v];[1:a]loudnorm=I=-14:TP=-1.5:LRA=11[bgm]" -map "[v]" -map "[bgm]" -c:v libx264 -ar 48000 -ac 2 -shortest final.mp4

# 5) 中/英双外挂字幕「仅本地预览」：B站投稿在创作中心单独上传 .srt，不读 mp4 内嵌轨
ffmpeg -i final.mp4 -i sub.zh.srt -i sub.en.srt -map 0 -map 1 -map 2 -c copy -c:s mov_text multi_sub_preview.mp4
```

### 4. 交付前 QC 清单（每项附检查方法）
- [ ] 字幕无溢框、无错别字、中英时间轴对齐 — 播放抽帧目检 + 逐字校对 .srt；`ffprobe -v error -show_entries subtitle_stream=index,codec_name` 查字幕流
- [ ] A/V 同步、无音画漂移 — 抽帧对比口播时间轴；`ffprobe` 查各流 duration/start_time 是否一致
- [ ] 编码合规（MP4/H.264/AAC，分辨率/帧率达标）— `ffprobe -v error -show_entries stream=codec_name,width,height,r_frame_rate,nb_frames` 核对
- [ ] 无配音版含 BGM/音效轨且响度归一 — `ffprobe` 查音频流存在；`ffmpeg` loudnorm 打印报告核对 I≈-14
- [ ] 真人配音文案时长与成片匹配（逐镜校验通过）— 公式逐镜校验
- [ ] 封面尺寸合规、文字可读、无被遮挡 — 读图查尺寸 + 目检
- [ ] 全片无英文闲杂词；片尾"AI"已改「人工智能」— 全文检索 + 片尾帧目检

## 实测记录
2026-09-20 Windows/Git Bash + ffmpeg 9.0.1 冒烟：全链 9/9 通过；发现并修复 PlayRes 384×288 与 -shortest 两处配方缺陷（已写入上文硬规则与配方）；响度实测 -14.0 LUFS；中文字幕（Microsoft YaHei 64px）底部安全区渲染目检合格。scripts/ 两脚本（pipeline.sh、fix_ass_style.py）为实测产物。
