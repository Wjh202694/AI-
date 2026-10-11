# splash-anim-template

网页开屏动效模板与验证工作流。抖音／大疆 Pocket 广告风格：刀刃劈开 → 辅轨展开 → 三环光圈晕开转清晰。当前版本 **v26**（v25 提速基础上做三环错峰：外→次→内 0.30s 相位差出生、外−内间距峰值拉大）。

## 触发场景

- 要做网页开屏动效、转场动效、光圈晕开效果
- 要修改／迭代已有的开屏动效模板
- 需要一条可换背景图的通用开屏模板

## 文件结构

| 路径 | 说明 |
| --- | --- |
| `SKILL.md` | 技能主文档：模板结构、动画时序、参数含义、验证流程 |
| `assets/splash_template.html` | 源模板（含 `__BG__` / `__SFX__` 占位符） |
| `assets/开屏特效_通用模板.html` | 可直接打开的成品（通用背景版） |
| `assets/build_splash.py` | 构建脚本：模板 → 单文件成品（base64 注入背景图） |
| `assets/build_universal.py` | 通用模板构建脚本 |
| `assets/patch_v23.py` … `patch_v26_stagger.py` | 各版本原子补丁脚本（断言式替换，跑完 grep 校验零旧痕迹） |
| `assets/ab_v23_2.py`、`ab_v24_2.py`、`parse_v23.py` | A/B 对比与版本解析辅助 |
| `assets/smoke16.js`、`smoke26.js`、`v23_freeze.js`、`v24_freeze.js`、`v26_freeze.js` | 浏览器冒烟验证：加载页面、冻结指定时间点、截图 |
| `assets/universal_check.js` | 通用模板校验脚本 |

## 使用方法

**环境变量**：所有 Python 脚本读取 `WORKSPACE`（原为硬编码绝对路径，已改为环境变量以保证可移植）：

```bash
export WORKSPACE=/path/to/your/project   # Windows: set WORKSPACE=C:\path\to\project
```

- 构建成品：`python assets/build_splash.py`
- 迭代改造：`python assets/patch_v26_stagger.py`
- 验证渲染：`node assets/smoke26.js`（需 Playwright／浏览器环境）

## 版本演进

v23 基础骨架 → v24 提速 → v25 全局提速（移除音效，改为剪辑软件后期配乐）→ v26 三环错峰。当前无音频元素，录屏后自行配乐更灵活。
