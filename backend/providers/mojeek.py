# -*- coding: utf-8 -*-
"""Mojeek 开放爬虫搜索（search.mojeek.com，免密钥，无追踪）。

适合作为 Brave 不可达时的英文资料兜底。
"""

from typing import List

import httpx
from bs4 import BeautifulSoup

from .base import SearchProvider
from .. import config


class MojeekProvider(SearchProvider):
    name = "mojeek"

    async def search(self, query: str, max_results: int = 8) -> List[dict]:
        headers = {
            "User-Agent": config.DESKTOP_UA,
            "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
        }
        params = {"q": query}
        try:
            async with httpx.AsyncClient(
                timeout=config.SEARCH_TIMEOUT, follow_redirects=True, headers=headers
            ) as client:
                resp = await client.get("https://www.mojeek.com/search", params=params)
        except Exception:
            return []
        if resp.status_code != 200:
            return []
        resp.encoding = "utf-8"
        return self._parse(resp.text, max_results)

    def _parse(self, html: str, max_results: int) -> List[dict]:
        soup = BeautifulSoup(html, "lxml")
        results: List[dict] = []
        for li in soup.select("ul.results-standard li, ol.results-standard li, li.result"):
            a = li.find("a", href=True)
            if not a:
                continue
            url = a["href"]
            if not url.startswith("http"):
                continue
            title = a.get_text(strip=True)
            cap = li.select_one("p.s, .desc")
            snippet = cap.get_text(strip=True) if cap else ""
            results.append({"title": title, "url": url, "snippet": snippet[:300]})
            if len(results) >= max_results:
                break
        return results
