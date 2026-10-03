# skillopt-officeqa

官方文档问答与计算技能。检索官方时间序列／表格数据，建立单一数据源。

## 通用特征

`skillopt-*` 系列是一组**任务型技能**：为特定基准／任务形态定义严格的作答纪律，核心是「证据优先、纪律优先、格式优先」。每个技能只负责一种任务类型，内部按小节拆解该类型的专属纪律。

## 使用方式

当作任务契约使用：命中该任务类型时加载对应技能，严格遵守其中的纪律小节。

## 纪律小节

- **Retrieval Discipline**——检索纪律，先取原文再作答
- **Evidence Discipline**——证据必须可追溯
- **Final Answer Discipline**——最终答案格式纪律
- **Statistical and Time-Series**——统计与时间序列题的专门规则
- **Stricter Final Formatting**——最终输出格式的更严格要求

## 文件结构

```
skillopt-officeqa/
└── SKILL.md    # 全部纪律小节（单文件）
```
