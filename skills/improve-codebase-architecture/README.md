# improve-codebase-architecture

扫描代码库寻找**架构深化机会**（把浅模块变深模块的重构），以可视化 HTML 报告呈现，然后针对你选中的那一项进入拷问式 grilling 循环。目标是提升可测试性与 AI 可导航性。

## 触发场景

- 明确要求扫描代码库架构问题（`disable-model-invocation: true`，需显式调用）
- 想找出"哪里该重构、怎么重构"

## 三段式流程

1. **Explore**——读取 `CONTEXT.md`（领域模型语言）与 `docs/adr/`（既有决策，不重新翻案），扫描代码库找 shallow module
2. **Present candidates as a visual HTML report**——把候选项渲染成 HTML 可视化报告供挑选
3. **Grilling loop**——针对选中的候选项逐条拷问：范围、风险、验证方式、抽象边界

## 依赖

- 架构词汇表（module / interface / depth / seam / adapter / leverage / locality）来自 `codebase-design` skill
- 若未安装该 skill，核心扫描与报告流程仍可运行，仅缺少统一术语表

## 文件结构

```
improve-codebase-architecture/
├── SKILL.md              # 主流程
├── HTML-REPORT.md        # 报告模板与渲染规范
└── agents/openai.yaml    # 智能体配置
```
