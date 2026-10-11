# -*- coding: utf-8 -*-
"""360 搜索（www.so.com，免密钥）。"""

from typing import List
from urllib.parse import urlparse, parse_qs

import httpx
from bs4 import BeautifulSoup

from .base import SearchProvider
from .. import config


class So360Provider(SearchProvider):
    name = "so360"

    async def search(self, query: str, max_results: int = 8) -> List[dict]:
        headers = {
            "User-Agent": config.DESKTOP_UA,
            "Accept-Language": "zh-CN,zh;q=0.9",
        }
        params = {"q": query}
        try:
            async with httpx.AsyncClient(
                timeout=config.SEARCH_TIMEOUT, follow_redirects=True, headers=headers
            ) as client:
                resp = await client.get("https://www.so.com/s", params=params)
        except Exception:
            return []
        if resp.status_code != 200:
            return []
        resp.encoding = "utf-8"
        return self._parse(resp.text, max_results)

    def _parse(self, html: str, max_results: int) -> List[dict]:
        soup = BeautifulSoup(html, "lxml")
        results: List[dict] = []
        for li in soup.select("li.res-list, div.res, li.result"):
            h3 = li.find(["h3", "h4"])
            a = None
            if h3:
                a = h3.find("a") if h3.name != "a" else h3
            if not a or not a.get("href"):
                continue
            href = a["href"]
            if "so.com/link" in href:
                qs = parse_qs(urlparse(href).query)
                real = qs.get("url", [""])[0]
                if real:
                    href = real
            url = href
            title = a.get_text(strip=True)
            cap = li.select_one(".res-desc, .res-summary, p")
            snippet = cap.get_text(strip=True) if cap else ""
            results.append({"title": title, "url": url, "snippet": snippet[:300]})
            if len(results) >= max_results:
                break
        return results
