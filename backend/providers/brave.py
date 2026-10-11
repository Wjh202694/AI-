# -*- coding: utf-8 -*-
"""Brave Search 公开 HTML 版（search.brave.com，免密钥）。

适合海外资料 / 国际视角查询；中文结果质量一般。
"""

from typing import List

import httpx
from bs4 import BeautifulSoup

from .base import SearchProvider
from .. import config


class BraveProvider(SearchProvider):
    name = "brave"

    async def search(self, query: str, max_results: int = 8) -> List[dict]:
        headers = {
            "User-Agent": config.DESKTOP_UA,
            "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
        }
        params = {"q": query, "source": "web"}
        try:
            async with httpx.AsyncClient(
                timeout=config.SEARCH_TIMEOUT, follow_redirects=True, headers=headers
            ) as client:
                resp = await client.get("https://search.brave.com/search", params=params)
        except Exception:
            return []
        if resp.status_code != 200:
            return []
        return self._parse(resp.text, max_results)

    def _parse(self, html: str, max_results: int) -> List[dict]:
        soup = BeautifulSoup(html, "lxml")
        results: List[dict] = []
        # Brave 结果用 div.snippet 包裹
        for div in soup.select("div.snippet, div#results div.snippet"):
            a = div.find("a", href=True)
            if not a:
                continue
            url = a["href"]
            if url.startswith("/"):
                continue  # 跳过内部跳转
            title_el = div.select_one("h2, .title, span.snippet-title")
            title = title_el.get_text(strip=True) if title_el else a.get_text(strip=True)
            snip = div.select_one(".snippet-description, .snippet-content, p")
            snippet = snip.get_text(strip=True) if snip else ""
            results.append({"title": title, "url": url, "snippet": snippet[:300]})
            if len(results) >= max_results:
                break
        return results
