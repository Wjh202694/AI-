# -*- coding: utf-8 -*-
"""DuckDuckGo 预留通道。

实测本机（中国大陆网络）html.duckduckgo.com 不可达，默认不启用。
保留实现以演示 SearchProvider 换源能力；海外环境可将 config 中开关打开。
"""

from typing import List

import httpx
from bs4 import BeautifulSoup

from .base import SearchProvider
from .. import config


class DuckDuckGoProvider(SearchProvider):
    name = "duckduckgo"

    async def search(self, query: str, max_results: int = 8) -> List[dict]:
        headers = {"User-Agent": config.DESKTOP_UA}
        async with httpx.AsyncClient(
            timeout=config.SEARCH_TIMEOUT, follow_redirects=True, headers=headers
        ) as client:
            resp = await client.post(
                "https://html.duckduckgo.com/html/", data={"q": query}
            )
        if resp.status_code != 200:
            return []
        resp.encoding = "utf-8"
        soup = BeautifulSoup(resp.text, "lxml")
        results: List[dict] = []
        for a in soup.select("a.result__a"):
            url = a.get("href", "")
            title = a.get_text(strip=True)
            parent = a.find_parent("div", class_="result")
            snip = parent.select_one(".result__snippet") if parent else None
            results.append({
                "title": title,
                "url": url,
                "snippet": snip.get_text(strip=True)[:300] if snip else "",
            })
            if len(results) >= max_results:
                break
        return results
