# -*- coding: utf-8 -*-
"""数据模型。"""

from typing import Any, Dict, List, Optional
from pydantic import BaseModel


class PlanRequest(BaseModel):
    question: str
    extra_terms: List[str] = []          # 前端 LLM 扩展词（可选）
    answers: Dict[str, Any] = {}         # 多角度追问的作答 {维度id: 选项值 / 选项值列表}


class QueryItem(BaseModel):
    group: str                            # A/B/C/D/E
    group_name: str                       # 原始问句/拆词组合/高级指令/站点定向/反面搜索
    query: str
    checked: bool = True
    note: str = ""                        # 说明文字


class ClarifyOption(BaseModel):
    value: str                            # 选项值（回传给 answers）
    label: str                            # 显示文字
    hint: str = ""                        # 小字说明
    group: str = ""                       # 互斥组名（同名互斥；空 = 不互斥）


class ClarifyPrompt(BaseModel):
    id: str                               # focus / time / stance / depth / scope
    dimension: str                        # 维度名（中文）
    text: str                             # 追问文字（grill-me 风格）
    options: List[ClarifyOption] = []     # 预设选项
    allow_free: bool = False              # 是否允许自定义填空
    free_hint: str = ""                   # 自定义占位提示


class PlanResponse(BaseModel):
    question: str
    terms: List[str]                      # 拆出的关键词（已据作答调整）
    jargon: List[str]                     # 命中的黑话扩展
    queries: List[QueryItem]
    clarify: List[ClarifyPrompt] = []     # 多角度追问
    refined: bool = False                 # 是否已在作答后细化


class SearchRequest(BaseModel):
    question: str
    queries: List[QueryItem]              # 用户勾选后的查询列表
    llm_used: bool = False
    terms: List[str] = []                 # 用于内容相关度判定（前端 plan 时已拆出）
    relevance_tier: Optional[Any] = None  # 允许任意类型（aggregate 内部兑底）
    relax_threshold: Optional[Any] = None  # 保留旧字段，优先级低于 relevance_tier


class ClickRequest(BaseModel):
    url: str


class LLMRequest(BaseModel):
    question: str
    terms: List[str] = []                 # 已拆出的关键词，供 LLM 改写参考


class SearchResult(BaseModel):
    channel: str                          # web / site
    grade: str = "unsure"                 # primary / unsure / secondary
    grade_label: str = "存疑·需交叉验证"
    title: str = ""
    url: str = ""
    snippet: str = ""
    domain: str = ""
    score: float = 0.0
    source_query: str = ""                # 命中它的查询
    is_counter: bool = False              # 是否来自反面搜索组
    local_path: str = ""                  # 知识库结果的本地路径
    provenance_note: str = ""             # 为何判此级（溯源说明）
    stale: bool = False                   # 距今超过 3 年
    is_official_deep: bool = False        # 一手站点官方直达
    relevance: str = "high"               # high / relaxed / low（内容相关度）
    relevance_reasons: str = ""           # 内容相关度判定明细（UI 鼠标悬浮可看）


class ChannelStatus(BaseModel):
    channel: str
    ok: bool
    message: str = ""
    count: int = 0


class SearchResponse(BaseModel):
    search_id: int
    question: str
    results: List[SearchResult]
    status: List[ChannelStatus]
    stats: dict                           # {"primary": n, "unsure": n, "secondary": n, "counter": n}
    ask_relax: bool = False               # 保留字段：过滤后 0 条时为 True
    relax_threshold: float = 0.0          # 当前使用的阈值
    relevance_tier: str = ""              # 当前档位（strict / balanced / loose）
    filtered_total: int = 0               # 抓取前总条数
