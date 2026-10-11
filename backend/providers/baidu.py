# -*- coding: utf-8 -*-
"""百度备用通道（反爬兜底）。解析失败仅返回空，不再上抛。"""

from typing import List

import httpx
from bs4 import BeautifulSoup

from .base import SearchProvider
from .. import config


class BaiduProvider(SearchProvider):
    name = "baidu"

    async def search(self, query: str, max_results: int = 8) -> List[dict]:
        headers = {
            "User-Agent": config.DESKTOP_UA,
            "Accept-Language": "zh-CN,zh;q=0.9",
        }
        params = {"wd": query, "rn": str(max_results)}
        async with httpx.AsyncClient(
            timeout=config.SEARCH_TIMEOUT, follow_redirects=True, headers=headers
        ) as client:
            resp = await client.get("https://www.baidu.com/s", params=params)
        if resp.status_code != 200:
            return []
        resp.encoding = "utf-8"
        return self._parse(resp.text, max_results)

    def _parse(self, html: str, max_results: int) -> List[dict]:
        soup = BeautifulSoup(html, "lxml")
        results: List[dict] = []
        for div in soup.select("div.result, div.c-container"):
            h3 = div.find(["h3"])
            a = h3.find("a") if h3 else None
            if not a or not a.get("href"):
                continue
            # 百度结果链接是 www.baidu.com/link?url=... 跳转，原样保留并注明域名
            url = a["href"]
            title = a.get_text(strip=True)
            cap = div.select_one(".c-abstract") or div.find("p")
            snippet = cap.get_text(strip=True) if cap else ""
            results.append({"title": title, "url": url, "snippet": snippet[:300]})
            if len(results) >= max_results:
                break
        return results
