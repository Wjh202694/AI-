---
name: ui-award-design
version: 1.1.0
display_name: 获奖级 UI 设计
description: 参考 Awwwards / React Bits / MotionSites 的高质感 UI 设计技能，产出获奖级视觉与动效，并用 web-design-guidelines 做真实渲染无障碍审计。分工：要求获奖级/强动效用本 skill；普通 UI 审计直接用 web-design-guidelines。触发词：获奖级 UI、Awwwards、React Bits、MotionSites、高级动效、品牌站、落地页设计。
read_when:
  - 需要获奖级 / 高审美 UI 与动效
  - 用户提到 Awwwards、React Bits、MotionSites 或高级交互
  - 在产出界面后做 WCAG 无障碍审计
---

# 获奖级 UI 设计

## 分工声明（避免与同类 skill 重叠）
- 本 skill：要求**获奖级视觉 / 强动效 / 品牌记忆点**时使用。
- 普通 UI 无障碍审计：直接用 skill: web-design-guidelines（当前 v2.1.0）。
- 本环境尚有 design-taste-frontend、frontend-design 等同栈 skill；凡未明确要「获奖级/动效」的需求，优先让主会话选用更轻量的那个，避免重复加载。

## 功能定位
以国际前沿设计站为参考系，产出高质感、强动效、有记忆点的界面；并用 web-design-guidelines（当前 v2.1.0）全部规则做**真实渲染**后的无障碍兜底，做到「好看且可用」。

## 参考源
- Awwwards（https://www.awwwards.com）：获奖网站画廊，交互/排版/动效趋势基准。
- React Bits（https://www.reactbits.dev）：开源 React + Tailwind 组件与动画，可直接复用（前提栈匹配，见规则）。
- MotionSites（https://www.motionsites.io 或同类动效站合集）：滚动叙事与微交互范例。

## 工作流
1. 明确需求：平台（Web/移动）、品牌调性、参考风格关键词。
2. 检索参考：
   - **首选内置库**「附录 A：获奖级设计模式库」（已蒸馏的排版尺度、间距节奏、动效 token、标志性模式），直接取用，不依赖实时抓取。
   - 需更新灵感时，用 web-search / 图片搜索取具体案例图（Awwwards 等重 JS 站 WebFetch 抓不到有效内容，不要硬抓）。
3. 产出界面：HTML/CSS/组件（深色/浅色主题、响应式、动效）。
   - 栈为 React+Tailwind：优先复用 React Bits 组件。非 React 栈：**提取模式而非代码**。
4. 真实渲染审计：见「环境依赖 + 降级」的真实渲染审计执行路径（本地起静态服务 → agent-browser 渲染 → axe/Lighthouse）。通过线见验收标准。
5. 修复 CRITICAL/HIGH 项（语义 HTML、对比度、键盘导航、reduced-motion）。

## 性能预算（现实约束）
- 动画只用 `transform` / `opacity` 合成层属性，避免触发 layout/paint。
- 单页主包体积预算（按需设上限，如 JS ≤ 200KB gz）；长列表/大图走懒加载。
- 帧率目标 60fps；掉帧动效降级为简单过渡。

## 中文字体策略（中文场景）
- 完整 CJK webfont 是 MB 级，必须**子集化**（仅打包用到的字）或走**系统字体栈**（`"PingFang SC","Microsoft YaHei",sans-serif`）。
- 不得默认加载完整中文字体文件；图标优先用 SVG/Iconfont 子集。

## 输入
- 需求描述 / 草图 / 竞品链接
- 品牌色、字体、目标平台、无障碍等级（AA 底线）
- 风格关键词（如 glassmorphism / brutalist / neumorphism）

## 输出
- 界面代码（HTML/CSS/React 组件）
- 设计稿截图（通过 agent-browser HTML 渲染 → 截图产出）
- 无障碍审计报告（web-design-guidelines v2.1.0 全部规则 PASS/FAIL + Top3 优先修复）
- 动效说明（进场/交互动效、reduced-motion 降级方案）

## 关键规则
- 动效服务于内容，不炫技；必须实现 `prefers-reduced-motion` 降级。
- 视觉前沿 ≠ 牺牲可用性；对比度、焦点态、ARIA 标签不可省。
- React Bits 复用前提是 React+Tailwind 栈；非 React 项目改为「提取模式」。
- 参考站仅作灵感来源，不得直接抄袭；二次创作并注明借鉴点。
- **模式库回填**：每次实际交付后，把用到的 1–2 个新/调整过的模式补回附录 A（附来源与适用栈），使库随使用变厚。

## 环境依赖 + 降级
- 依赖：agent-browser（真实渲染+截图/审计）、web-design-guidelines（v2.1.0，审计规则）、可选 web-search（取参考图）。
- 真实渲染审计执行路径：
  - 起本地静态服务：`python -m http.server 8080`（file:// 协议下 Lighthouse 不可用）。
  - Lighthouse：`npx lighthouse http://localhost:8080 --only-categories=accessibility --output=json`（需 Node 环境，npx 即用）。无 Chrome 时 `CHROME_PATH` 指向 Edge（Windows 风格路径 `'C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe'`，实测可用），加 `--chrome-flags="--headless=new"`。
  - axe：用 agent-browser 的 `eval`（注意：命令名是 eval，不是 evaluate）注入 axe-core CDN（`https://cdn.jsdelivr.net/npm/axe-core/axe.min.js`），执行 `axe.run()` 读取 violations；也可直接跑 `scripts/axe-audit.sh <url>`（实测：axe 4.13）。
  - agent-browser 首次运行 daemon 冷启动较慢，`open` 卡住时 stop 后重试一次再判失败。
- 降级：
  - 无 agent-browser / 无 lighthouse → 注入 axe-core CDN 脚本读 violations + 人工清单兜底，并在报告中标注未真实渲染 Lighthouse、结论置信度降低。
  - 无 web-design-guidelines → 停止审计，仅交付设计稿并提示缺审计依赖。

## 验收标准
- 真实渲染通过线：**Lighthouse accessibility ≥ 90** 且**文本对比度达 WCAG AA**（4.5:1 正文 / 3:1 大字）。无法跑 Lighthouse 时，以 axe violations = 0（CRITICAL/HIGH）为替代通过线。
- 动效均含 `prefers-reduced-motion` 分支。
- 性能：动效仅用合成层属性；主包体积以构建产物 JS 总体积 ≤ 上限（如 200KB gz）为判据（可用 `npx vite build` 后查 dist 体积或 webpack-bundle-analyzer；无构建工具时人工清单核对并标注未自动检测）。
- 中文字体已子集化或走系统栈，无完整 CJK 字体硬加载。

## 协作（给主会话的指令）
- 真实浏览器验证建议主会话调用 skill: web-avatar-subagent（网页替身）。
- 封面/品牌视觉可与 skill: video-bilibili-shorts（B站短视频制作）互供。

---

## 附录 A：获奖级设计模式库（蒸馏自 Awwwards / React Bits / MotionSites）

> 直接取用，不依赖实时抓取参考站。新增模式时附来源与适用栈；每次交付后回填用过的模式。

### 1. 排版尺度
- 建立 1.25（大屏）~1.2（移动）模块化比例（modular scale），标题用 clamp() 流式缩放：`font-size: clamp(2rem, 5vw, 4rem)`。
- 正文 16–18px，行高 1.6；展示型大标题可到视口宽度的 8–12%。

### 2. 间距节奏
- 8px 基准栅格（8/16/24/32/48/64）。区块间距优先 64/96/128。
- 用 CSS 变量统一：`--space-1:8px … --space-6:64px`。

### 3. 动效 Token
- 时长：微交互 150–200ms，进场 400–600ms，页面过渡 500–800ms。
- 缓动：标准 `cubic-bezier(0.16,1,0.3,1)`（ease-out-expo 感）；弹性 `cubic-bezier(0.34,1.56,0.64,1)`。
- 仅用 `transform` / `opacity` 合成层属性。

### 4. 标志性模式
- **滚动驱动揭示（scroll-driven reveal）**：元素进入视口时淡入+上移；用 IntersectionObserver，配 `prefers-reduced-motion` 关闭。
- **磁性按钮（magnetic button）**：鼠标靠近时元素微位移跟随（`transform: translate`），离开回弹。
- **文字逐行/逐字进场**：按词或行拆分，stagger 延迟入场。
- **页面过渡（page transition）**：遮罩滑入/内容交叉淡入，保持导航连续性。
- **光标跟随（custom cursor）**：小圆点+外环延迟，hover 可交互元素时放大。
- **英雄区版式（hero layouts）**：居中留白型 / 左右分栏型 / 全幅媒体型；大标题 + 一句话价值主张 + 单一主 CTA。
- **视差 / 滚动叙事（parallax / scroll narrative）**：`transform: translateZ` + perspective 或 scroll-linked 变量驱动多层差速移动。
- **图像颗粒与遮罩揭示（grain & mask reveal）**：SVG `mask` / `clip-path` 擦除揭示，叠加 noise/grain 纹理提升质感。
- **全屏导航（fullscreen nav）**：overlay 菜单，链接 stagger 进场，配模糊背板。
- **卡片 hover 语汇（card hover）**：lift/tilt（3D 倾斜）、glare（高光跟随）、scanline（扫描线）等。

### 5. 配色与留白
- 主色 + 中性灰阶 + 1 个强调色；深色模式用 `#0b0b0f` 级背景，避免纯黑。
- 留白即呼吸：内容最大宽度 1200–1280px，两侧留白 ≥24px。

### 6. 响应式断点
- 移动 <768 / 平板 768–1024 / 桌面 >1024；动效在移动端大幅削减（省电、防卡）。

### 7. 中文场景注意
- 字体走系统栈或子集化，禁用完整 CJK 字体硬加载。
- 中文排版行高略放宽至 1.7–1.8；标点用全角，标题避免孤字换行。

## 实测记录
2026-09-20：本地 http.server + agent-browser 0.38.1 注入 axe-core 4.13 全链通过，测试页 5 类埋点问题（button-name critical、color-contrast/html-has-lang serious、landmark/region moderate）全数命中；Lighthouse 以 Edge 为内核（CHROME_PATH）跑通，评分与 axe 结果一致。scripts/axe-audit.sh 为实测产物。
