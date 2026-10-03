# skillopt-spreadsheetbench

Excel/xlsx 结构化操作技能。用 openpyxl + pandas 在 `solution.py` 里处理工作簿，保持与目标匹配的稳健输出。

## 通用特征

`skillopt-*` 系列是一组**任务型技能**：为特定基准／任务形态定义严格的作答纪律，核心是「证据优先、纪律优先、格式优先」。每个技能只负责一种任务类型，内部按小节拆解该类型的专属纪律。

## 使用方式

当作任务契约使用：命中该任务类型时加载对应技能，严格遵守其中的纪律小节。

## 小节结构

- Overview / Common Workflow
- **Library Selection**——openpyxl 与 pandas 的选择依据
- **solution.py Template**——脚本模板
- Output Requirements / Matching and Target Range——输出必须匹配目标格式与范围
- **Robustness for Simple Fills**——简单填充场景的稳健性处理

## 环境依赖

Python + `openpyxl` + `pandas`

## 文件结构

```
skillopt-spreadsheetbench/
└── SKILL.md    # 全部小节（单文件）
```
