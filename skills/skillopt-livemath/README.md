# skillopt-livemath

数学选择题精确作答技能。比较选项逻辑强度、核查量词与条件阈值、避免常见陷阱。

## 通用特征

`skillopt-*` 系列是一组**任务型技能**：为特定基准／任务形态定义严格的作答纪律，核心是「证据优先、纪律优先、格式优先」。每个技能只负责一种任务类型，内部按小节拆解该类型的专属纪律。

## 使用方式

当作任务契约使用：命中该任务类型时加载对应技能，严格遵守其中的纪律小节。

## 纪律小节

- **Option Comparison**——逐项对比选项的逻辑强度
- **Meta-Options About Stronger Claims**——识别"更强命题"类元选项
- **Theorem-Level Precision**——定理级精度要求
- Hypotheses / Exact Conditions and Thresholds——条件与阈值必须精确
- Final Answer / Exact Scope and Quantification——最终答案的范围与量词约束

## 文件结构

```
skillopt-livemath/
└── SKILL.md    # 全部纪律小节（单文件）
```
