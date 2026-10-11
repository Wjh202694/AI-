# caveman

极简压缩通信模式。像穴居人一样说话，token 用量降低约 **75%**，但技术准确性完全保留。

## 触发场景

- 用户说「caveman mode」「talk like caveman」「少说废话」「省 token」
- 需要极高信息密度的技术沟通
- 显式调用 `/caveman`

## 强度等级

| 等级 | 说明 |
| --- | --- |
| `lite` | 轻度压缩，保留完整句式 |
| `full` | 默认档，砍掉所有冗余修饰 |
| `ultra` | 极简，只留结论与关键参数 |
| `wenyan-lite` / `wenyan-full` / `wenyan-ultra` | 文言文风格三档 |

## 核心规则

- **技术实质全部保留**：只删 fluff（铺垫、客套、情绪铺垫词）
- 句子压到最短，一句一个意思
- 代码、命令、参数、数字、路径原样保留，不做任何"简化"
- 存在 `Auto-Clarity` 机制：信息可能丢失时自动切回清晰表达，避免误读
- 有 `Boundaries`：不压缩需要精确性的内容（安全提示、法律条款、关键配置）

## 文件结构

```
caveman/
└── SKILL.md    # 全部规则（含 Persistence、Rules、Intensity、Auto-Clarity、Boundaries）
```
