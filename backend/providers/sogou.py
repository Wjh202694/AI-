# -*- coding: utf-8 -*-
"""搜狗搜索（web.sogou.com，免密钥）。"""

from typing import List

import httpx
from bs4 import BeautifulSoup

from .base import SearchProvider
from .. import config


class SogouProvider(SearchProvider):
    name = "sogou"

    async def search(self, query: str, max_results: int = 8) -> List[dict]:
        headers = {
            "User-Agent": config.DESKTOP_UA,
            "Accept-Language": "zh-CN,zh;q=0.9",
        }
        params = {"query": query}
        try:
            async with httpx.AsyncClient(
                timeout=config.SEARCH_TIMEOUT, follow_redirects=True, headers=headers
            ) as client:
                resp = await client.get("https://www.sogou.com/web", params=params)
        except Exception:
            return []
        if resp.status_code != 200:
            return []
        resp.encoding = "utf-8"
        return self._parse(resp.text, max_results)

    def _parse(self, html: str, max_results: int) -> List[dict]:
        soup = BeautifulSoup(html, "lxml")
        results: List[dict] = []
        # 搜狗结果卡片：div.vrwrap 或 div.rb
        for div in soup.select("div.vrwrap, div.rb, div.result"):
            h3 = div.find(["h3", "a"])
            a = None
            if h3 and h3.name == "a":
                a = h3
            elif h3:
                a = h3.find("a")
            if not a or not a.get("href"):
                continue
            href = a["href"]
            # 搜狗结果带链接跳转，跳过同站链接
            if "sogou.com/link" in href:
                # 真实 URL 在 /link?url= 参数里
                from urllib.parse import urlparse, parse_qs
                qs = parse_qs(urlparse(href).query)
                real = qs.get("url", [""])[0]
                if real:
                    href = real
            url = href
            title = a.get_text(strip=True)
            cap = div.select_one(".vr-title, .rb-content, .abstract, p")
            snippet = cap.get_text(strip=True) if cap else ""
            results.append({"title": title, "url": url, "snippet": snippet[:300]})
            if len(results) >= max_results:
                break
        return results
