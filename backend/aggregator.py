# -*- coding: utf-8 -*-
"""多 provider 并发编排 + 内容相关度过滤 + 点击量排序。

2026-10 改造：
- 多搜索引擎并发：Bing / 百度 / 搜狗 / 360 / Brave / Mojeek / DDG
- 主 provider 跑全部 query；备用 provider 跑前 3 条；总条数收敛
- 内容相关度过滤 + grade 分桶 + clicks 排序
- 0 条兜底：返回 ask_relax=True
"""

import asyncio
import random
import re
from typing import List, Optional, Tuple
from urllib.parse import urlparse

from . import clicks, config, fetch, grader, site_search
from .models import ChannelStatus, QueryItem, SearchResult
from .providers import (BaiduProvider, BingProvider, BraveProvider, DuckDuckGoProvider,
                         GitHubProvider, MojeekProvider, OpenAlexProvider,
                         ProviderBlocked, So360Provider, SogouProvider,
                         ToutiaoProvider, WeixinSogouProvider)


# 每个 provider 在每个 query 上的最大结果数（控制总条数）
_PROVIDER_MAX_RESULTS = {
    "bing":       5,   # 主源：跑全部 query
    "baidu":      3,   # 中文备用
    "weixin":     3,   # 微信公众号文章
    "toutiao":    3,   # 字节系（今日头条/西瓜/抖音）— 时事/资讯
    "openalex":   3,   # 学术论文元数据（OpenAlex 索引）
    "github":     2,   # 代码仓库
    "sogou":      3,   # 国内反爬严格，默认走 bing/baidu/weixin，备选
    "so360":      3,   # 国内反爬严格，默认走 bing/baidu/weixin，备选
    "brave":      3,   # 英文 / 国际资料（国内连接可能不可达）
    "mojeek":     2,   # 英文兜底
    "duckduckgo": 2,   # 海外兜底
}
# 备用 provider 跑前几个 query（主 provider 跑全部）
_FALLBACK_QUERY_LIMIT = 2
# 同一 query 内多 provider 串行间隔（防反爬）
_PROVIDER_GAP = (0.15, 0.4)


def _normalize_url(url: str) -> str:
    try:
        p = urlparse(url)
        host = p.netloc.lower()
        host = host[4:] if host.startswith("www.") else host
        path = p.path.rstrip("/")
        return f"{host}{path}".lower()
    except Exception:
        return url.lower()


def _is_cninfo_query(query: str) -> bool:
    return "cninfo.com.cn" in query


def _clean_site_query(query: str) -> str:
    return re.sub(r"site:\S+", "", query).strip()


def _all_providers():
    """列出所有内置 provider；任何一路失败都不阻塞其他路。"""
    return [
        ("bing",      BingProvider()),
        ("baidu",     BaiduProvider()),
        ("weixin",    WeixinSogouProvider()),
        ("toutiao",   ToutiaoProvider()),
        ("openalex",  OpenAlexProvider()),
        ("github",    GitHubProvider()),
        ("sogou",     SogouProvider()),
        ("so360",     So360Provider()),
        ("brave",     BraveProvider()),
        ("mojeek",    MojeekProvider()),
        ("duckduckgo", DuckDuckGoProvider()),
    ]


async def _run_provider(name: str, provider, queries: List[QueryItem],
                         max_per_query: int, gap: bool = True) -> List[SearchResult]:
    """单 provider 跑一组 query；任一条失败/反爬则跳过该条，不影响其他。"""
    out: List[SearchResult] = []
    for qi in queries:
        try:
            raw = await provider.search(qi.query, max_per_query)
        except ProviderBlocked as e:
            # 主源被反爬就立即放弃该 provider，其他 provider 继续跑
            if name == "bing":
                break
            continue
        except Exception:
            continue
        channel = "site" if qi.group == "D" else "web"
        for r in raw:
            out.append(_to_result(r, channel, qi))
        if gap:
            await asyncio.sleep(random.uniform(*gap))
    return out


async def _run_web_channel(queries: List[QueryItem]) -> Tuple[List[SearchResult], List[ChannelStatus]]:
    """所有 provider 并发；主 provider 跑全部 query，备用跑前 3 条。"""
    statuses: List[ChannelStatus] = []
    tasks = []

    for name, prov in _all_providers():
        max_r = _PROVIDER_MAX_RESULTS.get(name, 4)
        qset = queries if name == "bing" else queries[:_FALLBACK_QUERY_LIMIT]
        tasks.append((name, qset, max_r, prov))

    # 并发跑所有 provider
    raw_lists = await asyncio.gather(
        *[_run_provider(n, p, q, m, gap=_PROVIDER_GAP) for (n, q, m, p) in tasks],
        return_exceptions=True,
    )

    all_results: List[SearchResult] = []
    for (name, _, _, _), res in zip(tasks, raw_lists):
        if isinstance(res, Exception):
            statuses.append(ChannelStatus(channel=name, ok=False, message=str(res)[:80], count=0))
            continue
        all_results.extend(res)
        if res:
            statuses.append(ChannelStatus(
                channel=name, ok=True,
                message=f"{name} 命中 {len(res)} 条",
                count=len(res),
            ))
        else:
            statuses.append(ChannelStatus(
                channel=name, ok=False,
                message=f"{name} 无结果或不可达",
                count=0,
            ))
    return all_results, statuses


async def _run_cninfo(queries: List[QueryItem]) -> Tuple[List[SearchResult], ChannelStatus]:
    """巨潮补充通道：对 D 组中 cninfo 查询调其官方接口。"""
    if not any(_is_cninfo_query(qi.query) for qi in queries if qi.checked):
        return [], ChannelStatus(channel="site", ok=True, message="未启用（无站点定向查询）", count=0)
    out: List[SearchResult] = []
    for qi in queries:
        if not _is_cninfo_query(qi.query):
            continue
        kw = _clean_site_query(qi.query)
        if not kw:
            continue
        raw = await site_search.cninfo_search(kw)
        for r in raw:
            out.append(_to_result(r, "site", qi))
    if out:
        return out, ChannelStatus(channel="site", ok=True,
                                 message=f"一手站点命中 {len(out)} 条（官方直达）", count=len(out))
    return out, ChannelStatus(channel="site", ok=False, message="一手站点无命中", count=0)


def _to_result(r: dict, channel: str, qi: QueryItem) -> SearchResult:
    g = grader.grade_result(r.get("title", ""), r.get("url", ""), r.get("snippet", ""), channel)
    return SearchResult(
        channel=channel,
        grade=g["grade"], grade_label=g["grade_label"], score=g["score"],
        title=r.get("title", ""), url=r.get("url", ""),
        snippet=r.get("snippet", ""), domain=g["domain"],
        source_query=qi.query, is_counter=(qi.group == "E"),
        provenance_note=g["provenance_note"], stale=g["stale"],
        is_official_deep=g["is_official_deep"],
    )


async def _apply_content_filter(results: List[SearchResult],
                                terms: List[str],
                                threshold: float) -> Tuple[List[SearchResult], int, List[dict]]:
    """并发抓正文 + 多维度内容相关度评估。

    返回 (保留结果, 被过滤数, 元信息列表)。
    """
    if not results:
        return [], 0, []
    if not terms:
        return results, 0, []
    urls = [r.url for r in results]
    pairs = await fetch.fetch_many_with_meta(urls)
    kept: List[SearchResult] = []
    dropped = 0
    metas: List[dict] = []
    for r, (html, text) in zip(results, pairs):
        if not text:
            dropped += 1
            metas.append({"url": r.url, "passed": False, "reasons": ["抓取失败"]})
            continue
        meta = fetch.assess(html, text, r.title or "", terms, threshold=threshold)
        metas.append({"url": r.url, "title": r.title,
                      "passed": meta["passed"], "relevance": meta["relevance"],
                      "reasons": meta["reasons"],
                      "ratio": meta["ratio"], "hit": meta["hit"], "total": meta["total"]})
        if meta["passed"]:
            # 动态拓宽：保存 relevance 到 SearchResult 里，UI 标记边缘相关
            r.relevance = meta["relevance"]
            r.relevance_reasons = " · ".join(meta["reasons"])
            kept.append(r)
        else:
            dropped += 1
    return kept, dropped, metas


_GRADE_ORDER = {"primary": 0, "unsure": 1, "secondary": 2}


def _sort_results(results: List[SearchResult], click_counts: dict) -> List[SearchResult]:
    """grade 分桶 → 桶内按点击量降序。"""
    def _key(r: SearchResult):
        return (_GRADE_ORDER.get(r.grade, 99),
                -int(click_counts.get(r.url, 0)))
    return sorted(results, key=_key)


async def aggregate(question: str, queries: List[QueryItem],
                    terms: Optional[List[str]] = None,
                    relevance_tier: Optional[str] = None,
                    relax_threshold: Optional[float] = None):
    """主入口：多 provider 并发 → 内容相关度过滤 → 点击量排序。

    返回 (results, status, stats, meta)。

    安全网：任何阶段异常都返回部分结果 + 状态信息，不面 500。
    """
    # 入参健全性检查：避免空查询 / 空问题导致的隐性失败
    if not question or not question.strip():
        raise ValueError("问题不能为空")
    if not queries or not any(q.checked for q in queries):
        raise ValueError("请至少勾选一条查询")

    checked = [q for q in queries if q.checked]
    status = []
    final = []
    raw_total = 0
    dropped = 0
    tier = config.DEFAULT_RELEVANCE_TIER
    threshold = config.RELEVANCE_TIERS[tier]

    try:
        web_task = _run_web_channel(checked)
        cninfo_task = _run_cninfo(checked)
        (web_results, web_statuses), (cninfo_results, cninfo_status) = await asyncio.gather(
            web_task, cninfo_task
        )
        status = web_statuses + [cninfo_status]

        # 去重（URL 归一化），保留分数最高的一条
        seen = {}
        for r in (web_results or []) + (cninfo_results or []):
            try:
                key = _normalize_url(r.url) if r.url else r.title
                if key not in seen or r.score > seen[key].score:
                    seen[key] = r
            except Exception:
                continue
        raw_all = list(seen.values())
        raw_total = len(raw_all)

        # 档位解析：仅接受白名单值，其他一律兑底默认档
        if isinstance(relevance_tier, str) and relevance_tier in config.RELEVANCE_TIERS:
            tier = relevance_tier
            threshold = config.RELEVANCE_TIERS[tier]
        elif isinstance(relax_threshold, (int, float)) and 0 < relax_threshold <= 1:
            threshold = float(relax_threshold)
            tier = "custom"
        else:
            tier = config.DEFAULT_RELEVANCE_TIER
            threshold = config.RELEVANCE_TIERS[tier]

        # 内容过滤（容错：单条失败不中断整体）
        try:
            kept, dropped, _ = await _apply_content_filter(raw_all, terms or [], threshold)
        except Exception:
            # 过滤失败时兑底返回原始列表（仅去重后的）
            kept = raw_all
            dropped = 0
            status.append(__import__('backend.models', fromlist=['ChannelStatus']).ChannelStatus(
                channel="filter", ok=False, message="内容过滤异常，已兑底返回原始结果", count=0))

        # 读取点击量（容错）
        try:
            click_counts = clicks.get_counts([r.url for r in kept])
        except Exception:
            click_counts = {}

        # 排序（容错）
        try:
            final = _sort_results(kept, click_counts)
        except Exception:
            final = list(kept)

    except Exception as e:
        # 最外层容错：任何未预期的异常都返回空结果 + 错误状态
        status.append(__import__('backend.models', fromlist=['ChannelStatus']).ChannelStatus(
            channel="system", ok=False,
            message=f"聚合异常：{type(e).__name__}: {str(e)[:120]}",
            count=0))

    stats = {
        "primary": sum(1 for r in final if getattr(r, 'grade', '') == "primary" and not getattr(r, 'is_counter', False)),
        "unsure": sum(1 for r in final if getattr(r, 'grade', '') == "unsure" and not getattr(r, 'is_counter', False)),
        "secondary": sum(1 for r in final if getattr(r, 'grade', '') == "secondary" and not getattr(r, 'is_counter', False)),
        "counter": sum(1 for r in final if getattr(r, 'is_counter', False)),
    }
    meta = {
        "ask_relax": False,
        "relax_threshold": threshold,
        "relevance_tier": tier,
        "filtered_total": raw_total,
        "filtered_kept": len(final),
        "filtered_dropped": dropped,
    }
    return final, status, stats, meta
