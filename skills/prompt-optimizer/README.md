# prompt-optimizer

创建、优化、迭代 agent prompt / system prompt / developer prompt。以契约化步骤产出可直接使用的成品，而非泛泛建议。

## 触发场景

- 要写／改 agent 的系统提示词
- 现有 prompt 输出不稳定、啰嗦、漏关键约束
- 需要针对特定模型做适配

## 六步流程

| 步骤 | 产出 |
| --- | --- |
| 1. Capture Contract | 明确受众、目标、约束、验收条件 |
| 2. Inventory External Constraints | 盘点平台能力、权限、工具限制 |
| 3. Choose Model Strategy | 按模型特性选择适配策略 |
| 4. Shape Prompt | 结构化组织指令（硬性要求／优先偏好／可选增强分层） |
| 5. Optimize | 压缩冗余、把模糊词转成可观察标准 |
| 6. Return Package | 输出整合后的完整成品 |

另含 **Failure Modes** 章节：列出会导致 prompt 失效的典型模式。

## 文件结构

```
prompt-optimizer/
├── SKILL.md                        # 主流程
├── SOURCES.md                      # 依据来源
└── references/
    ├── core-patterns.md            # 核心模式库
    ├── meta-optimization-loop.md   # 元优化循环
    ├── model-family-notes.md       # 各模型家族特性
    └── transformed-examples.md     # 改写前后对照样例
```

> 使用提示：`references/` 体积较大，按需加载（`Load Only What You Need`）。
