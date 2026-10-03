# skillopt-alfworld

ALFWorld 文本具身环境任务技能。在纯文本家庭场景中，按可行动作列表完成目标。

## 通用特征

`skillopt-*` 系列是一组**任务型技能**：为特定基准／任务形态定义严格的作答纪律，核心是「证据优先、纪律优先、格式优先」。每个技能只负责一种任务类型，内部按小节拆解该类型的专属纪律。

## 使用方式

当作任务契约使用：命中该任务类型时加载对应技能，严格遵守其中的纪律小节。

## 小节结构

- Overview / Task Types
- Pick Two Object Bookkeeping
- General Principles
- Common Mistakes to Avoid
- **Hard Search-Loop Recovery**——搜索陷入循环时的恢复策略
- Strict Search Ledger Actions

## 文件结构

```
skillopt-alfworld/
└── SKILL.md    # 全部纪律小节（单文件）
```
