---
name: splash-anim-template
description: 网页开屏动效（抖音大疆 Pocket 广告风：刀刃劈开→辅轨展开→三环光圈晕开转清晰）的模板复用与验证工作流。当用户要求制作网页开屏动效、转场动效、光圈晕开效果，或要修改/迭代既有开屏动效模板时使用。当前为 v26（v25 提速 + v26 三环错峰：外→次→内 0.30s 相位差出生、外−内间距峰值拉大、次−内一次交叉、外−次单调增），另含可换背景图的通用模板套件。
agent_created: true
version: 2.3.0
---

# 网页开屏动效模板（v26：三环错峰 + 全局提速；2.2.0 起无音效）

单文件 HTML 开屏动效：主轨底部劈开→展宽→0.7s 上伸 → 辅轨三相位展开（对角生长→4/7 长方形→铺满）→ 三环光圈自中心一个很小的点晕开（水波涟漪：淡阴影→≈2.02s 追平转亮带）→ 全屏转清晰。背景图 base64 注入。2.2.0 起音效整体移除（无 audio 元素、无 sfxUrl 配置），录屏后自行在剪辑软件配乐更灵活。

## 资产清单（assets/）

| 文件 | 用途 |
|---|---|
| `splash_template.html` | 模板源（v26 态，`__BG__` 占位符 ×8，改这里不改最终产物） |
| `build_splash.py` | 构建脚本：base64 背景注入 `__BG__`，断言占位符数量后生成最终 HTML |
| `v26_freeze.js` | 冻结验证（当前）：`__splashSeek(t)` 冻结 11 个时间点（1.30~2.95），Node 端重现 v26 公式逐点 DOM 断言 + 7 组间距/错峰/阴影/终态/速度连续性断言，输出 V26JSON |
| `patch_v26_stagger.py` | v26 错峰补丁（断言式原子替换：注释块改写 + 3 处公式替换，终检新旧 token） |
| `smoke26.js` | v26 回放冒烟（当前）：首播 done / overflow 恢复 / splash 隐藏 / 重播 / seek 公式复核 / pageerror 捕获 |
| `v24_freeze.js` / `v24_ab.js` + `ab_v24_2.py` | v24 水波涟漪冻结验证与像素 A/B 留档 |
| `v23_freeze.js` / `v23_ab2.js` / `ab_v23_2.py` | v23 差速模型留档（贴轨光圈 + slack） |
| `parse_v23.py` | 解析 playwright-cli 输出 JSON（处理 JS 转义） |
| `smoke16.js` | 回放冒烟（v16/v24 旧目标留档；v26 用 smoke26.js） |
| `patch_v23.py` / `patch_v24.py` / `patch_v25_speed.py` | 补丁脚本范式：断言式原子替换留档 |
| `开屏特效_通用模板.html` | **通用模板**：CONFIG.bgImage 单点换图（CSS 变量 --bg）、speed、showSkip；头部注释含三种用法文档 |
| `build_universal.py` + `patch_universal.py` + `universal_check.js` | 通用模板打包器（base64 内联出离线单文件）/ 派生补丁 / 两模式验证脚本 |

## 工作流

1. **改模板**：只改 `splash_template.html`（CSS/HTML/JS 三段都在其中）。改后必须跑 `build_splash.py` 重新生成最终 HTML——如果增删了带背景图的元素，同步更新 `assert` 里的 `__BG__` 数量（当前 8）。
2. **冻结验证**：`npx @playwright/cli@latest open --browser=msedge --headed && npx @playwright/cli@latest run-code --filename v26_freeze.js`（必须 && 串联，daemon 跨命令不存活）。脚本冻结 1.30~2.95s 共 11 点，输出 V26JSON（problems 数组内嵌断言结果）。
3. **像素 A/B**：`v24_ab.js` 对同一冻结帧截两帧（正常 vs `addStyleTag` 强制去掉某层滤镜）并导出渲染几何 JSON，stdout 重定向到文件后 `python ab_v24_2.py < 输出文件` 逐点比值。这是验证滤镜真实效果的唯一可靠手段。
4. **冒烟**：`smoke26.js` 跑回放完整性（evaluate click 版，见硬坑 23），完事 `npx @playwright/cli@latest close`。
5. **目检**：冻结帧 PNG 对照参考图，重点看涟漪小点起步、环边界、阴影浓度、亮带宽度。

## 关键参数（v24 水波涟漪定稿时间轴）

- 主轨：0.30s 劈开 / 0.50s 展宽 / 0.50→1.20 outCubic 上伸；粗细恒 `vw/36`（HALF=vw/72）
- 辅轨：1.26→2.56s 单一 easeOutQuad（`e=1-(1-u)²`），u≈0.336（t≈1.70）长方形落定
- **光圈三环水波涟漪（v24）**：单一半径曲线 `r = maxR×1.08 × inOutQuad((t-1.26)/1.69)`，起止速度均为 0（1.30s≈1px 小点、1.42s≈14px 慢起步、2.95s 收满出屏）；`rm=0.87r`（外-次间距 0.13r 单调增大，用户点名的"间距逐渐增大"）；内圈 `rc=r(1-k)`，`k=0.46-0.43·smoothstep((t-1.30)/1.05)`（0.54r 清晰小点同生→≈2.02s 追平次外圈→亮带渐宽，2.35s 带 60px）；`sh=clamp01((rm-rc)/26)`（峰值≈0.84）
- **停顿感根因（v23→v24 教训）**：入场 ramp `×clamp01((tt-1.26)/0.12)`（1.38s 速度骤降 ~850px/s）与 slack 二段加速（2.00s 速度二次断崖）是仅有的两个停顿源；单一 inOutQuad 曲线全时段最大 Δv≈11px/s 彻底消除。v23 差速贴轨模型留档在 git 式注释里
- **全局提速（v25）**：`SPEED=0.8` 只加在 `t=(now-t0)/1000*SPEED` 唯一入口（所有相位等比压缩、曲线连续性不变）；`__splashSeek` 同步改 `(t/SPEED)*1000` 保持「时间轴秒」语义 → 冻结脚本零改动；finish 阈值 4.65→4.75（给 vanish CSS 淡出留缓冲）。加速后：劈开 0.24s / 涟漪 1.01s / 辅轨满屏 2.05s / 光圈收满 2.36s / 定格 2.76s / 收尾完毕 ≈3.7s
- **通用模板三件套**：CONFIG.bgImage → `setProperty('--bg', url(...))` + `.scene img` src JS 注入（8 处 __BG__ = 7 处 CSS var + 1 处 img src）；`build_universal.py` 把 CONFIG.bgImage 替换为 dataURI 出离线单文件；换图只需改 CONFIG 一行或同目录放 bg.jpg
- **三环错峰（v26，当前定稿）**：三环全部由主曲线派生（独立曲线+延迟会让近端速度比 1.25>1 破坏外−次单调，弃）。次外圈张开式 `ms=ss((t-1.56)/0.35); rm=r·(1-0.13ms)`（出生贴外圈内缘，外−次间距 0.13·ms·r 单调增）；内圈窗口换移 `ks=ss((t-1.74)/1.21); kk=0.50-0.42ks; rc=r·(1-kk)`（外−内峰≈0.21R@2.30，≈2.69 内圈反超次外恰一次，终距 0.08r 终态序 r>rc>rm）；错峰淡入 oI=(t-1.26)/0.10、oM=(t-1.56)/0.12、oC=(t-1.86)/0.12（外→次→内相邻 0.30 相位）。1920×1080 实测：peakOI=276.8px@2.30、peakMI=173.9px、终态亮带 62.7px、速度跳变 jR/jOM/jMI=17.6/16.6/22.1（阈值 35/60/60）
- 亮带：`.core-bright` z3 + `brightness(1.12)`；core 尺寸=`min(rc,rm)`；阴影 `sh=clamp01((rm-rc)/26)` 交叉前可感知、交叉后归零（2.69 起）
- 滤镜：.iris `blur(12px) saturate(1.4) brightness(1.06)`；.mid `blur(3.5px) brightness(1-0.14sh)`；辅轨 `grayscale(1) brightness(1.32) contrast(.92) blur(3px)`

## 硬坑（每条都踩过，直接背）

1. **#world 有 `scale(1.07)` 背景漂移**：所有渲染几何 ×1.076。像素采样坐标必须来自 `getBoundingClientRect()` 导出的渲染值，按 CSS px 算会整体错位（症状：A/B 比值恒 1.0 假阴性——采样点落进别的层）。
2. **无头渲染不可信**（假象帧/clip-path 不渲染）：验证一律 `--headed` + 截图。
3. **playwright-cli**：open 与 run-code 必须 && 串联；`wait networkidle` 会因持续动画永久挂起（改 open+sleep）；会话坏了 TaskStop 杀掉别恋战。**open 命令拦截 file:// 协议**（Access to "file:" protocol is blocked）——本地文件先用 `python -m http.server <port> --bind 127.0.0.1` 起服务再 open http://127.0.0.1:port/…，测完 netstat 找 PID taskkill；run-code 里的 page.goto(file://) 不受此限。
4. **filter 会把元素 box-shadow 整体模糊**：环亮缘必须独立 `.edge` 层（border+发光），不能挂在带 filter 的层上。
5. **overflow:hidden 裁剪边 AA 会混入下层颜色**：裁剪边下层必须是同源内容垫层（slitPad 模式：1.26s 起交叉渐变 0.03s 接管，两层逐像素同源无闪变）。
6. **动画曲线必须解析求导验证速度连续性**（数值采样步长会漏断崖——v20 停顿教训）。
7. **截图为设备像素**：本机 DPR 1.5，PNG 坐标 ×1.5。
8. **playwright-cli 返回 JSON 的引号被 JS 转义显示**：解析前 `replace('\\"','"')` 再 `raw_decode`。
9. **elementFromPoint 跳过 pointer-events:none 层**（iris-clip/aux 全是）——查遮挡用 elementsFromPoint 看堆栈，别误判光圈层被盖。
10. **测量暗线用 A/B 同帧对比**（同 x 去滤镜 vs 正常），整列均值剖面会误报（aux 只覆盖部分行高）。
11. **bgCover 手动 cover 数学**（scale=max(vw/IW,vh/IH)，position=视口图偏移−盒偏移）保证跨图层像素对齐，新层必须调用它而不是 background-size:cover。
12. **补丁断言词必须是代码 token 不是叙述词**：旧痕迹断言用 `slack` 这种短词会命中自己新写的注释（"…与 slack 二段加速…已删除"）导致补丁误报失败；断言一律用 `var slack`、`(maxR * 1.14` 这类只可能出现在代码里的长 token。
13. **涟漪/晕开类曲线只用单曲线**：凡是"先入场 ramp 再接二段加速"的组合必然产生速度断崖（人眼对匀速偏差极敏感，症状即"衔接停顿感"）；起止速度均为 0 的 inOutQuad 单曲线 + 比例包络（k 值 smoothstep）是零停顿的标准解。
14. **playwright 截图路径必须用绝对路径**：相对路径按 daemon 启动时的 cwd 解析（从 .workbuddy 里 open 会落进 .workbuddy/.workbuddy/ 嵌套目录）。
15. **run-code 的脚本是 Node 上下文**：顶层没有 document/getComputedStyle，页面查询必须包在 `page.evaluate(() => {...})` 里（症状：ReferenceError: document is not defined）。
16. **改全局时长只动 t 的唯一入口**：`t=(now-t0)/1000*SPEED` 一处缩放即可等比压缩全部相位；千万不要逐段改常量（破坏曲线衔接）；CSS transition（vanish 0.65s）是挂钟时间不随 SPEED 缩放，finish 阈值要给它留缓冲。
17. **注入/截取模板 CSS 时防 @media 未闭合**：用 index/slice 截 CSS 尾段时，`tpl.index("}", tpl.index("{ display: none; }"))` 会匹配到**内层**声明块的 `}`，把外层 @media 闭合括号截掉 → 未闭合 @media 吞掉其后全部规则（症状：注入的合成背景层/按钮样式在正常浏览器全失效、只剩纯黑底=全程黑屏）。截取锚点要写成完整串 `"display: none; } }"` 再 +len。
18. **注入类改动冒烟必须像素级**：状态机标志（busy/ls/display）全绿 ≠ 画面正确；至少截「动画中段一帧」用眼验非黑非透明。另：blackout 是静态垫底层（无衰减代码），黑→亮靠辅轨铺满盖掉；playwright-cli 每次会话是新 profile，localStorage 不跨会话，帧验证脚本必须自带 setItem。
19. **真机（手机）端先算合成层预算**：全视口克隆栈数 × scale × DPR² 是纹理内存的乘法关系，iOS/安卓 WebView 超预算会**静默丢层**（层透明露黑底，桌面 DPR1 复现不了）。降级三板斧：≤720px 砍装饰克隆（柔渐变+blur 下无对位可感差异）、雾层去大 blur、栈尺寸 JS 设 innerWidth/innerHeight（真机 100vh 含地址栏 ≠ innerHeight，必须同源）+ resize 重设。确定性验证用 `__splashSeek(t)` 冻结帧，别跟挂钟时序较劲。
20. **丝滑动画的铁律：布局属性与 filter 都是每帧毒药**。带 filter（blur）的层尺寸/内容每帧变 = blur 每帧整层重光栅化（卡顿首因，×DPR² 放大）；正确姿势：内容盒尺寸恒定化（blur 一次光栅化）+ 几何动画全部改走 `clip-path`（inset/circle）/`transform`/`opacity` 合成器路径；filter 值每帧变（如动态 brightness）同样重光栅化——改恒定 filter+用 opacity 叠加模拟。改完用 rAF delta 统计（p50/p95）+ 冻结帧半径 vs 公式做形态学验证（探针 play→seek 连调有竞态，对照帧可能丢层不可信）。
21. **固定盒架构的两条契约**：①`reset()` 绝不能清 layoutOnce 固定的盒尺寸（width/height='0px' 会让每帧只写 clip-path 的层整个落空）——reset 只重置 clipPath 全裁/opacity/transform，几何归 layoutOnce 管；②**探针必须覆盖完整播放时序**（起播→铺满→vanish→finish→退场后一级界面恢复 + pageerror/console 捕获），只 seek 中段帧会漏掉 reset 破坏、收尾不退场这类只影响"播完之后"的回归；采样断言要对照时间轴换算（高刷下 180 帧 rAF 可能只走了 1.2s 时间轴，读到的是 reset 初值不是 bug）。
22. **"展开后是什么画面"要回答内容层，不只是几何层**：克隆/栈内容只有背景（宣纸+山峦）时，铺满期=一片白（UI 不在克隆里），用户看到的是"白屏不是界面"。栈内容应为**目标界面完整 cloneNode**（去 id/on* 防冲突误触；重模糊层保留纯背景省光栅化）；特效自带品牌字与克隆内真品牌会叠加，二选一隐藏。克隆的 CSS 入场动画会重播（秒级，与铺满时刻错开即无碍）；播放期给底层真身 visibility:hidden（省一整层合成，finish 必须恢复）。
23. **克隆层静止化 + GPU 合成带宽三主犯**：克隆内容里的**无限循环动画**（漂浮图/雾）每份克隆每帧全量重合成——克隆可见的时刻（往往正是中段）GPU 带宽陡增，表现为"到某一阶段开始卡"。修法：`.fx-stack .克隆 .漂浮元素{animation:none !important}` 只停无限动画、保留一次性入场（播完即静）；world 容器每帧位移（drift）=整棵树每帧重合成，宁可停掉（静态 scale 防露边）；每帧 clip-path/transform 写入改 **~10Hz 节流 + `transition: .13s linear` 引擎插值**（Chromium M116+ clip-path 可合成插值；seek 用专用 class `transition:none!important` + 强制 reflow 后移除）。判断标准：主线程 rAF p50 低≠不卡，**真机瓶颈在 GPU 合成带宽，层数×动画×位移才是乘法项**。
24. **判"画面炸了"先采真身对照**：截图见"巨大/偏移/裁半"的元素，先 `getBoundingClientRect` 对照真身同元素（差值恰为祖先 scale 即正常）、再查站点排版本身（左对齐标题被展开窗口裁半=设计互动非 bug）；`elementFromPoint` 命中≠视觉顶层（pointer-events:none 的层不可命中但可见）。
25. **冻结断言别在出生期查严格单调/正数**：间距曲线在窗口起点前恒为 0（如 t≤1.56 时 gapOM=0），两个零值间「严格递增」必误报——出生期放宽为非降、窗口起点后（如 1.70 起）才查严格增；整点出生时刻（t=1.86 整 oC=0）是淡入窗口起点，此刻断言应要求 ===0 而非 >0（查增长改看下一采样点）。
26. **playwright page.click 对全屏动画层有 hit-test 竞态**：done 后点 replayBtn，page.click 的 actionability 检查可能报「slitIn intercepts pointer events」反复重试到 30s 超时，而 elementFromPoint 实测按钮无遮挡、evaluate click 全链路正常——冒烟脚本一律用 `page.evaluate(() => el.click())` 绕过 hit-test。
27. **卡顿修完仍卡，就对照原版找架构性差异**：v4 把合成带宽三主犯（克隆动画/drift/每帧几何写入）修完仍卡 → 对照原版模板逐层排查，根因是注入版漏定义环层的 `--bg` 变量，被迫用全屏克隆栈撑环层内容（12 个 rMax 大盒常驻纹理）。对齐两刀：①环层自带 background（渐变+底图 cover）+ 栈 display:none，圆裁剪交给 clip-path circle（冗余 border-radius:50% 可删）；②收尾坍缩——涟漪出屏后（t≥3.1）三窗+环层全部退场，`#fxfull` 单层同像素克隆 opacity 接管（reset 必须恢复坍缩状态），收尾期大层 16→4。方法论：**性能问题先问原版为什么快**（全片一层 UI + 小盒背景），层数冗余是架构病，逐帧优化救不了。
28. **clip-path 动画在含克隆父层上无法走合成层——只有节流便宜，任何提升都更贵**：实测矩阵（同一站点）——逐帧裸写 13.8ms/43jank；全层 translateZ 提升 25.7ms（层爆炸）；30Hz+transition 16.3ms（transition 不合成、每写重绘）；仅提升克隆子层 .fx-stack 12.6ms（无效）；提升含克隆的裁剪父层 23.3ms（嵌套提升+clip=整子树每帧重合成，最灾难）。**正确解=自适应时间窗节流**：只把动画最快段（涟漪峰值速度区间）设为逐帧写入，其余 10Hz；配合扩展预热（所有揭示层+核心克隆在黑幕下全开预光栅化两帧）灭中途首次揭示尖峰。另两坑：①探针每帧 getComputedStyle 会以恒定 ~54ms p95 污染帧时测量——帧时必须用纯 rAF 间隔探针；②playwright headed 软件渲染帧时不可复现（同代码 8.6↔14ms），细调别依赖其数值，靠结构推理+冻结帧目检。
29. **收尾坍缩的一次性克隆必须前移到页面载入期建，幂等哨兵别用 st.firstChild**：v5/v6 把环层揭示改 transform:scale 后绽放窗已降到 ~6-9ms，残余尖峰是收尾坍缩（t≥3.1）时一次性 `cloneNode` 整页 `#splash` 并光栅化模糊克隆（~230ms 单帧尖峰）。修法：把 fxfull 整页克隆从「坍缩时懒建」挪到**页面载入期**（#splash 处于静止初态、黑幕掩护不可见），坍缩块改直接接管（buildFxfullClone 幂等）。**两坑**：①幂等哨兵绝不能用 `st.firstChild`——`#fxfull` 初始 `.fx-stack` 自带 `bg-art`/`fx-mist` 子节点 → 永远 truthy → 克隆函数提前 return、克隆永不构建（视觉退化为空层）；改用 `fxc.dataset.fxbuilt` 标志位，构建前先 `while(st.firstChild) removeChild` 清掉初始 bg-art 再 append 整页克隆。②**绝不能在 warmup/play 里建克隆**——warmup 的 `reset()` 会把 #splash 子节点写成隐藏内联态，克隆会捕获错误初态；必须在脚本载入、reset 之前（#splash  pristine 静止态）建。验证：headless 下用 rAF 包裹测逐帧 **CPU 工作**（避开 rAF 节流对「帧间隔」的污染），max 应从 ~230ms 降到 <3ms、over16=0；DOM 断言克隆节点数>0 且 t≥3.1 时 `fxfullOn` 翻 true。
30. **主线程 CPU 探针救不了「真机莫名的卡」——瓶颈在 GPU 合成层预算，headless 复现不了**：v7b 把逐帧 CPU 压到 max 2.2ms/over16=0，headless 全绿，真机照样卡。根因不是逐帧 JS，而是**同时常驻的提升层过多 + 全视口 blur 滤镜 → 显存/合成带宽溢出**。判定法（不依赖真机）：①数 `will-change` 元素与全视口层——本例 ~33 个全视口合成层（环层 12 + clip 层 6 + 克隆栈 11 + world/iris-world 4 + 常驻 constellation 1），其中 11 个塞整页 `#splash` 克隆、多个带 `filter:blur`；②按 `层数和 × (视口×DPR²×4)` 估算显存：1440×900×DPR2 ≈ 20.7MB/层 ×33 ≈ 680MB，再算 blur 中间缓冲（×2~4）→ 直接打爆核显 1~2GB 共享显存 → 合成器丢帧。main-thread CPU 探针只量 JS/raster 主线程，GPU 丢帧它读不到，所以「自己测是丝滑、用户说卡」。修法是**砍预算不是砍逐帧**：P0 把 11 份克隆换成「首屏渲染后一次性快照成一张图」复用（clip/scale/blur 图片都便宜，且消除 clip-on-clone 反模式）；P1 删 `.fx-stack` 多余 `will-change`（浏览器自己提升即可，别每层都提）、把全视口 `filter:blur` 烘进静态背景图（去实时模糊 PASS）；P2 按 DPR≥2 / deviceMemory 低 走降级（克隆层→渐变，去 blur）。另注意：克隆在页面载入即拍，若此时 #splash 还没灌数据，克隆是空骨架 → 揭示面板只显示骨架而非真 UI（潜在视觉 bug，换成「渲染后再拍快照」一并解决）。
31. **`contain:paint` 给"很多全视口元素"等于反向操作——会强制每层独立合成 + 配 blur 子层 = 比不隔离更炸**：P0 给 `.fx-stack`（~11 个全视口栈）加 `contain:paint` 想"隔离重绘范围"，结果浏览器把每个栈提升成独立合成层，而栈内 `.fx-mist` 带 `filter:blur(34px)` → **11 路全视口 34px 模糊 PASS，比删掉的整页克隆还贵**。教训：`contain:paint`/`will-change` 只在「该元素确实要独自动画且内容轻」时用；给"一堆全视口 + 内部有 blur"的容器统一加 = 显存/带宽爆炸。正确解：①直接删这类容器的 `contain:paint`/`will-change`，让它们并入父层合成（不再各自成层）；②删子层冗余 blur（`fx-mist` 的 3~4 层软径向渐变本就极柔，34px 模糊纯属冗余，直接 `filter:none`）；③`mix-blend-mode:multiply` 在**全视口**层上会强制逐帧回读合成（最贵单算子），能去则去；④`will-change:transform` 别错配——是按 clip-path 揭示的容器（如 `.fx-iris-clip`）就别写 transform，写了它既没用又白白占一层。判定"仍是卡"的二次根因就用这四条扫一遍。
32. **"真机持续卡"别只盯逐帧——先 grep 全页找永动机式常驻开销**：前 4 轮把开场逐帧压到 2.2ms、砍了克隆/模糊，用户仍说卡。根因根本不在逐帧逻辑，而是**底层一个永不停止的全屏 `requestAnimationFrame` 循环（尘粒 canvas）**：循环退出条件写错——检查 `document.getElementById('splash').classList.contains('fx-done')`，但 `splash` 是一级界面本体（永不会拿 `fx-done`，那个 class 只加在 `#fxsplash` 开场遮罩上）→ 条件恒真 → 除非系统开"减少动态效果"，否则 `position:fixed;inset:0` 全屏 canvas 每帧 clearRect+重绘 ~130 粒子**永不停止**，且开场黑幕播放期间也在背后 60fps 重绘抢 GPU。排查顺序：①`grep -n "requestAnimationFrame\|setInterval\|infinite"` 摸全页所有常驻循环/动画；②逐个看退出条件是否真能命中（尤其错元素）；③canvas 类循环几乎永远是该停就停——给它加 **开场门控（黑幕进行中不绘制）+ 节流(~15fps，慢速微闪够用)+ `document.hidden` 即停 + visibilitychange 恢复**。这条优先级高于任何逐帧微调：一个永动机全屏 rAF 比整段开场逐帧还费资源，且 headless/CPU 探针完全读不到（它只量 JS 单帧，测不出"一直在跑"）。
33. **真机录屏是唯一裁判，clip-path 揭示在真机=「长冻结+跳帧」，唯一出路 counter-scale**：用户真机录屏（ffmpeg fps=10 抽帧 + PIL 帧间运动量 + tile 马赛克墙）揭示的卡顿形态不是低帧率（那会连续小步运动），而是**动画 90% 时间完全静止（motion≈0）+ 偶发单帧大跳变**——每帧 clip-path inset 变化强制重光栅整层（含 blur 克隆），真机单帧数百 ms，rAF 回调间隔被打爆；#28 的"逐帧 13ms 尖峰"在开发机无感、真机放大数十倍，#30 的"GPU 预算"只是共犯。修法（v9 定稿）：①**counter-scale 揭示**——窗口层 `overflow:hidden`（已有）+ 每帧 `transform:scale(sx,sy)`（origin=揭示矩形**固定角**，注意右块固定缘是底边 → origin y=vh），内容层反向 `scale(1/sx,1/sy)` 且 origin=窗口屏幕点−盒偏移 → 组合=恒等、像素零变形，纯合成器零重绘；sx clamp ≥0.0002；origin 由 layoutOnce 统一设（resize 重算）。inset→scale 换算：sx=(揭示宽)/vw、sy=(揭示高)/vh，缩放后窗口盒恰=揭示矩形。②**rAF 冻结检测保底**：frame 开头测 `now-lastNow`，连续 >220ms ×2 → 加 fx-lite；×5 → finish()（保证最坏=快点结束）；此时 rAF delta 检测**有效**（它测的就是渲染管线长帧）。③doClip 闸门失效化（transform 写入近零成本，恒逐帧）。验证：`__splashSeek` 冻结帧截图 + 白区宽度对照理论值（首检成功经验：agent-browser open 的 CLI 输出会被吞像挂死，但 daemon 存活，直接再发 `screenshot [selector] [path]`（positional 参数）与 `eval "js"` 即可）。
