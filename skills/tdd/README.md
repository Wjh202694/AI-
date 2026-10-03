# tdd

测试驱动开发（红 → 绿循环）。重点不是"怎么写测试"，而是让这个循环产出**值得留存**的测试：什么算好测试、测试该放在哪、常见反模式、循环的规则。

## 触发场景

- 用户要测试先行地构建功能或修 bug
- 提到「red-green-refactor」
- 需要集成测试

## 核心内容

- **What a good test is**——测试通过公开接口验证行为，而非实现细节；好测试读起来像规格说明
- **Seams: where tests go**——测试该落在哪些接缝上
- **Anti-patterns**——测试反模式清单
- **Rules of the loop**——红绿重构的循环规则

## 领域语言对齐

探索代码库时读取 `CONTEXT.md`（若存在），让测试名与接口词汇匹配项目领域语言；遵守 `docs/adr/` 中该区域的既有决策。

## 文件结构

```
tdd/
├── SKILL.md              # 主文档
├── mocking.md            # Mock 策略
├── tests.md              # 测试细则
└── agents/openai.yaml    # 智能体配置
```
