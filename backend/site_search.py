# -*- coding: utf-8 -*-
"""一手站点定向检索。

D 组查询（site:xxx）本身经 Bing 通道执行；此处额外接巨潮资讯网公开检索接口，
命中时作为补充结果返回。巨潮接口失败不影响主流程。
"""

from typing import List

import httpx

from . import config

CNINFO_API = "http://www.cninfo.com.cn/new/fulltextSearch/full"


async def cninfo_search(keyword: str, max_results: int = 5) -> List[dict]:
    """巨潮资讯网全文检索（上市公司公告/招股书/年报，强一手来源）。"""
    params = {"searchkey": keyword, "sdate": "", "edate": "", "isfulltext": "false",
              "sortName": "pubdate", "sortType": "desc", "pageNum": "1"}
    headers = {"User-Agent": config.DESKTOP_UA, "Referer": "http://www.cninfo.com.cn/"}
    try:
        async with httpx.AsyncClient(timeout=config.SEARCH_TIMEOUT, headers=headers) as client:
            resp = await client.get(CNINFO_API, params=params)
        if resp.status_code != 200:
            return []
        data = resp.json()
    except Exception:
        return []

    results: List[dict] = []
    for ann in (data.get("announcements") or [])[:max_results]:
        title = (ann.get("announcementTitle") or "").replace("<em>", "").replace("</em>", "")
        sec = ann.get("secName") or ""
        adjunct = ann.get("adjunctUrl") or ""
        url = f"http://static.cninfo.com.cn/{adjunct}" if adjunct else ""
        t = ann.get("announcementTime")
        date_str = ""
        if isinstance(t, (int, float)) and t > 0:
            import datetime
            date_str = datetime.datetime.fromtimestamp(t / 1000).strftime("%Y-%m-%d")
        results.append({
            "title": f"{sec}：{title}" if sec else title,
            "url": url,
            "snippet": f"巨潮资讯网 · {date_str} · 上市公司信息披露原文",
        })
    return results
