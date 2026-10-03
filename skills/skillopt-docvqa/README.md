# skillopt-docvqa

文档视觉问答（DocVQA）技能。精确回答：能从文档图像／扫描件中提取的最小精确答案。

## 通用特征

`skillopt-*` 系列是一组**任务型技能**：为特定基准／任务形态定义严格的作答纪律，核心是「证据优先、纪律优先、格式优先」。每个技能只负责一种任务类型，内部按小节拆解该类型的专属纪律。

## 使用方式

当作任务契约使用：命中该任务类型时加载对应技能，严格遵守其中的纪律小节。

## 纪律小节

- **Visual Evidence Discipline**——只用图像中确实可见的证据
- **Exact Answer Discipline**——只答能支撑的最小精确答案，不脑补
- **Structured Layout Lookup**——结构化版面（表格、多栏）定位规则
- Anchored Handwriting / Near-Ambiguous Text——手写体与模糊文本的处理锚点

## 文件结构

```
skillopt-docvqa/
└── SKILL.md    # 全部纪律小节（单文件）
```
