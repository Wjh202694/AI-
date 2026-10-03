# skillopt-searchqa

搜索题／知识竞赛精确问答技能。识别线索题型与答案类别、用检索证据作答。

## 通用特征

`skillopt-*` 系列是一组**任务型技能**：为特定基准／任务形态定义严格的作答纪律，核心是「证据优先、纪律优先、格式优先」。每个技能只负责一种任务类型，内部按小节拆解该类型的专属纪律。

## 使用方式

当作任务契约使用：命中该任务类型时加载对应技能，严格遵守其中的纪律小节。

## 纪律小节

- **Concise Answer Normalization**——答案归一化（单位、别名、格式）
- **Context-Grounded Evidence**——证据必须落在上下文中
- **Clue Interpretation and Answering**——线索解读规则
- **Trivia / Jeopardy Snippet Clues**——百科／竞猜式线索的解法
- **Common Clue Traps**——常见线索陷阱清单

## 文件结构

```
skillopt-searchqa/
└── SKILL.md    # 全部纪律小节（单文件）
```
