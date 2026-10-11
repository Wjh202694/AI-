# ui-award-design

获赞级 UI 设计。参考 Awwwards / React Bits / MotionSites 的高质感审美，产出视觉与动效都达标的界面，并用 web-design-guidelines 做真实渲染的无障碍兜底检查。

## 触发场景

- 需要获赞级／高审美 UI 与动效
- 用户提到 Awwwards、React Bits、MotionSites 或高级视觉
- 产品上线前做 WCAG 无障碍兜底

## 分工声明（避免与同类 skill 重叠）

视觉与动效由本 skill 负责；无障碍合规的深度检查交给 web-design-guidelines，两者互补不重叠。

## 关键约束

- **性能预算（现实约束）**：动效不得以牺牲真实可用性为代价
- **中文字体策略**：针对中文场景有专门的字体加载与回退方案
- 渲染兜底：用真实渲染检查，不用"看起来应该没问题"代替验证

## 文件结构

```
ui-award-design/
├── SKILL.md              # 工作流、约束、输入输出
└── scripts/axe-audit.sh  # 无障碍审计脚本
```
