# -*- coding: utf-8 -*-
"""全局配置：端口、路径、域名分级表、超时等常量。"""

from pathlib import Path

# ---- 路径 ----
ROOT_DIR = Path(__file__).resolve().parent.parent
FRONTEND_DIR = ROOT_DIR / "frontend"
DATA_DIR = ROOT_DIR / "data"
DB_PATH = DATA_DIR / "history.db"

# ---- 服务 ----
PORT_CANDIDATES = [8321, 8322, 8323]

# ---- 检索 ----
SEARCH_TIMEOUT = 6.0          # 单条查询超时（秒）
PROVIDER_TIMEOUT = 20.0       # 整个通道超时（秒）
MAX_RESULTS_PER_QUERY = 8     # 每条查询最多取回结果数
REQUEST_GAP = (0.3, 0.8)      # Bing 通道内部请求间隔随机区间（秒）

# ---- 内容相关度判定：3 档（默认宽松，让用户主动调严）----
MIN_HIT_RATIO = 0.80          # 严格档阈值
RELAX_HIT_RATIO = 0.60        # 平衡档阈值（兼容旧名）
RELEVANCE_TIERS = {
    "strict":   0.80,         # 严格：主要谈这个问题的文章
    "balanced": 0.60,         # 平衡：大部分内容谈这个问题
    "loose":    0.30,         # 宽松：只是提到这个问题的文章也能进
}
DEFAULT_RELEVANCE_TIER = "loose"  # 默认最宽松
MIN_SENTENCE_CHARS = 5        # < 此字符数的句子视为噪声，不计入分母
FETCH_CONCURRENCY = 10        # 抓正文并发数
FETCH_TIMEOUT = 3.0           # 单条正文抓取超时（秒）
FETCH_MAX_BYTES = 2 * 1024 * 1024  # 单次响应最大读取字节数，防止 PDF/巨型页吃内存

DESKTOP_UA = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/124.0.0.0 Safari/537.36"
)

# ---- 一手/二手分级：三层域名表 ----
# 一手白名单（强）：命中即"一手"
PRIMARY_DOMAINS = [
    "gov.cn",            # 各级政府网站（含 stats.gov.cn、mohrss、pbc、customs 等子域）
    "cninfo.com.cn",     # 巨潮资讯网（证监会指定信息披露）
    "sse.com.cn",        # 上交所
    "szse.cn",           # 深交所
    "hkexnews.hk",       # 港交所披露易
    "sec.gov",           # 美国证监会
    "arxiv.org",
    "nber.org",
    "edu.cn",            # 高校站点
    "chinacourt.org",
    "nssd.cn",           # 国家哲学社会科学文献中心
    "cnki.net",          # 知网（论文入口）
]

# 二手黑名单（自媒体/UGC 降权）
SECONDARY_DOMAINS = [
    "mp.weixin.qq.com",
    "toutiao.com",
    "baijiahao.baidu.com",
    "sohu.com",
    "163.com",
    "zhihu.com",
    "bilibili.com",
    "douyin.com",
    "xiaohongshu.com",
    "youtube.com",
    "weibo.com",
    "baike.baidu.com",
]

# 一手弱信号：标题/URL 命中加分
PRIMARY_HINT_WORDS = [
    "年报", "年度报告", "招股", "公告", "白皮书", "统计公报",
    "年鉴", "论文", "研报", "征求意见稿", "红头文件", "通知",
    "规划", "办法", "规定", "条例",
]

# 内容农场信号：降分
CONTENT_FARM_WORDS = ["震惊", "速看", "不看后悔", "刚刚", "突发！", "爆款"]

# ---- 行业黑话映射表（规则拆词用，可扩充）----
JARGON_MAP = {
    "工资": ["薪资", "薪酬", "人均可支配收入", "平均工资"],
    "收入": ["薪资", "人均可支配收入", "居民收入"],
    "政策": ["红头文件", "通知", "征求意见稿", "实施方案"],
    "公司": ["招股说明书", "年报", "营收", "财报"],
    "行业": ["行业报告", "白皮书", "市场规模", "渗透率"],
    "实习": ["实习招聘要求", "校招", "岗位职责"],
    "工作": ["招聘要求", "岗位职责", "任职资格"],
    "考研": ["研究生招生简章", "报录比", "复试分数线"],
    "考公": ["公务员招录公告", "职位表", "进面分数线"],
    "房价": ["商品住宅销售价格", "土地出让", "住房公积金"],
    "游戏": ["买量", "日活", "留存率", "版号"],
    "制造": ["良率", "产能", "代工", "供应链"],
    "人工智能": ["大模型", "算力", "参数量", "白皮书"],
    "ai": ["大模型", "人工智能", "算力"],
}

# 反面搜索触发词
COUNTER_WORDS = ["质疑", "反对", "风险", "失败", "争议", "后悔", "骗局", "问题"]

# 停用词（规则拆词时剔除）
STOP_WORDS = {
    "的", "了", "吗", "呢", "吧", "啊", "是", "我", "你", "他", "她", "它",
    "我们", "怎么", "怎么样", "如何", "什么", "为什么", "要不要", "该不该",
    "值得", "有没有", "可以", "应该", "想", "想问问", "请问", "一下", "还是",
    "现在", "真的", "到底", "究竟", "能", "会", "和", "与", "或", "在", "对",
    "对于", "关于", "一个", "一些", "大家", "人", "事", "东西",
}

# ---- 一手站点主题路由（站点定向组用）----
SITE_ROUTES = [
    {"topics": ["政策", "数据", "统计", "经济", "人口", "就业", "收入", "房价"],
     "site": "stats.gov.cn", "name": "国家统计局"},
    {"topics": ["公司", "股票", "上市", "财报", "招股", "行业", "企业"],
     "site": "cninfo.com.cn", "name": "巨潮资讯网"},
    {"topics": ["政策", "法规", "通知", "规定", "国务院"],
     "site": "gov.cn", "name": "中国政府网"},
    {"topics": ["论文", "研究", "学术", "实验"],
     "site": "arxiv.org", "name": "论文预印本库"},
]
