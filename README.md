# 搜绎 (Souyi)

> 把含糊的问题，理成能搜的话。

搜绎是一个本地优先的「智能检索助手」：用户在搜索框里输入含糊的问题（如「考研人数」「如何做决策」），搜绎会先通过多角度追问卡片帮用户把问题细化，然后并行调用多个搜索引擎（Bing / 百度 / 微信公众号 / 头条 / OpenAlex / GitHub 等）抓取候选页面，再用多维度判定过滤出**真正相关的**内容（≥80% 句子命中核心词）。

## 功能特性

- **多 Provider 并发检索**：Bing + 百度 + 微信 + 头条 + OpenAlex + GitHub 等 11 个数据源
- **多角度追问盘问卡片**：5 维度（核心指向 / 时间窗 / 立场 / 用途 / 范围），含多选 + 互斥分组
- **3 档内容相关度过滤**：严格 80% / 平衡 60% / 宽松 30%
- **多维度相关度判定**：句子命中率 + 标题含核心词 + 前 3 段含核心词 + 正文长度
- **用户点击量排序**：grade 分桶 + 同档按点击量降序
- **边缘相关警告标签**：放宽阈值后保留的内容打 `⚠️ 边缘相关` 标签
- **搜索历史 + Markdown 导出**：SQLite 存储历史记录，可导出 Markdown 笔记

## 技术栈

- **后端**：Python 3.13 / FastAPI / uvicorn / httpx / BeautifulSoup4
- **前端**：原生 JavaScript（无框架）
- **存储**：SQLite（搜索历史）+ 文件（数据缓存）
- **解析**：lxml（HTML 解析）

## 本地运行

```bash
# 安装依赖
pip install -r requirements.txt

# 启动服务（默认 http://127.0.0.1:8321/）
python main.py

# 或 Windows 用户双击 run.bat
```

## 云端部署（Railway）

1. 推送代码到 GitHub
2. Railway 上 `New Project` → `Deploy from GitHub repo` → 选本仓库
3. 配置环境变量（可选）：
   - `SOUYI_HOST=0.0.0.0`（云端必填，自动）
   - `SOUYI_GITHUB_TOKEN`（可选，提升 GitHub Search API 速率）
4. Railway 自动检测 Python 项目并部署
5. 部署完成后 Railway 会分配一个公网 URL（如 `xxx.up.railway.app`）

## 项目结构

```
search-agent/
├── main.py                # 入口
├── requirements.txt
├── railway.json           # Railway 部署配置
├── run.bat / stop.bat     # Windows 本地启动脚本
├── backend/               # FastAPI 后端
│   ├── app.py             # API 路由
│   ├── config.py          # 全局配置（含 3 档阈值）
│   ├── aggregator.py      # 多 provider 并发 + 过滤 + 排序
│   ├── fetch.py           # 抓取正文 + 多维度内容相关度判定
│   ├── clarifier.py       # 盘问卡片生成
│   ├── query_planner.py   # 查询矩阵生成
│   ├── grader.py          # 一手 / 二手分级
│   ├── history.py         # SQLite 历史记录
│   ├── clicks.py          # 用户点击量埋点
│   ├── models.py          # Pydantic 数据模型
│   └── providers/         # 11 个搜索 Provider
└── frontend/              # 原生 JS 前端
    ├── index.html
    ├── app.js
    └── style.css
```

## 配置说明

### 端口候选（`backend/config.py`）

```python
PORT_CANDIDATES = [8321, 8322, 8323]
```

### 内容相关度档位（3 档）

| 档位 | 阈值 | 默认 |
|---|---|---|
| `strict` | 80% | |
| `balanced` | 60% | |
| `loose` | 30% | ✓ 默认 |

### 搜索引擎覆盖

| Provider | 状态 |
|---|---|
| Bing | ✓ |
| 百度 | ✓ |
| 微信搜一搜 | ✓ |
| 头条搜索 | ✓ |
| OpenAlex 学术 | ✓ |
| GitHub 代码 | ✓ |
| 搜狗 / 360 / 神马 / 中国搜索 / Brave / Mojeek / DuckDuckGo | 保留代码备用 |

## 免责声明

本项目仅供个人学习与研究使用。请勿用于：
- 大规模商业爬虫
- 绕过网站服务条款
- 侵犯第三方权益

使用本项目产生的法律责任由使用者自行承担。
