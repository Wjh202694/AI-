# AI-

个人 AI 资产库。存放自制与自维护的 Agent Skill（技能包），以及个人 AI 相关的工具入口。

## 目录结构

```
AI-/
├── skills/       # Agent Skill 技能包（每个技能自带 README.md）
├── AI 入口启动器.lnk      # 原有：AI 入口快捷方式
└── 个人学习助手.lnk        # 原有：个人学习助手快捷方式
```

## 什么是 Agent Skill

一个技能包就是一个文件夹，核心是 `SKILL.md`（含 YAML frontmatter + 指令正文）：

- **`name`**——技能标识，调用时使用
- **`description`**——触发条件描述，决定何时被自动匹配
- 正文——这个技能被触发后的完整执行指令

把技能文件夹放进支持 skill 的 AI 工具的 skills 目录即可使用。

## 技能清单

### 设计与视觉

| 技能 | 简介 |
| --- | --- |
| [splash-anim-template](skills/splash-anim-template/) | 网页开屏动效模板（刀刃劈开→三环光圈晕开转清晰，v26 三环错峰） |
| [ui-award-design](skills/ui-award-design/) | 获赞级 UI 设计与动效，含性能预算与中文字体策略 |

### 工程实践

| 技能 | 简介 |
| --- | --- |
| [tdd](skills/tdd/) | 测试驱动开发：好测试的标准、测试接缝、反模式、循环规则 |
| [improve-codebase-architecture](skills/improve-codebase-architecture/) | 扫描架构深化机会，HTML 报告呈现 + 拷问式收敛 |
| [caveman](skills/caveman/) | 极简压缩通信模式，省 75% token |

### 提示词与协作

| 技能 | 简介 |
| --- | --- |
| [prompt-optimizer](skills/prompt-optimizer/) | agent prompt / system prompt 的契约化创建与优化（六步流程） |
| [conversation-handoff](skills/conversation-handoff/) | 多轮对话目标判断、漂移检测与上下文交接中枢 |
| [skill-router](skills/skill-router/) | 技能调用器：动手前先为任务找到正确的技能 |

### 内容与自动化

| 技能 | 简介 |
| --- | --- |
| [video-bilibili-shorts](skills/video-bilibili-shorts/) | B 站短视频流水线：中英双语字幕 + 无配音成片 + 配音文案 |
| [web-avatar-subagent](skills/web-avatar-subagent/) | 网页端任务替身：重型子任务委派独立子代理 |

### 任务型技能（skillopt 系列）

为特定基准／任务形态定义的严格作答纪律，一任务一技能：

| 技能 | 任务类型 |
| --- | --- |
| [skillopt-alfworld](skills/skillopt-alfworld/) | 文本具身环境任务（ALFWorld） |
| [skillopt-docvqa](skills/skillopt-docvqa/) | 文档视觉问答（DocVQA） |
| [skillopt-livemath](skills/skillopt-livemath/) | 数学选择题精确作答 |
| [skillopt-officeqa](skills/skillopt-officeqa/) | 官方文档问答与计算 |
| [skillopt-searchqa](skills/skillopt-searchqa/) | 搜索／知识竞赛精确问答 |
| [skillopt-spreadsheetbench](skills/skillopt-spreadsheetbench/) | Excel/xlsx 结构化操作 |

## 安装使用

将需要的技能文件夹复制到目标 AI 工具的用户级 skills 目录：

```bash
# 克隆本仓库
git clone https://github.com/Wjh202694/AI-.git

# 复制某个技能（以 splash-anim-template 为例）
cp -r AI-/skills/splash-anim-template ~/.workbuddy/skills/
```

各技能的具体用法见其目录内的 `README.md`。

## 约定

- 技能正文一律中文，技术标识符保留英文原样
- 涉及本机路径的脚本统一读 `WORKSPACE` 环境变量，不写死绝对路径
- 第三方来源的技能不在本仓库收录（避免版权与来源混淆）

## 说明

仓库中除 `skills/` 外，其余文件为个人本地快捷方式。
