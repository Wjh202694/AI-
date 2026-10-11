# -*- coding: utf-8 -*-
"""头条搜索（so.toutiao.com，免密钥）。

字节跳动自家的搜索引擎，覆盖今日头条 / 抖音 / 西瓜视频的内容。
适合时事、新闻、热点资讯类查询。
"""

from typing import List

import httpx
from bs4 import BeautifulSoup

from .base import SearchProvider
from .. import config


class ToutiaoProvider(SearchProvider):
    name = "toutiao"

    async def search(self, query: str, max_results: int = 8) -> List[dict]:
        headers = {
            "User-Agent": config.DESKTOP_UA,
            "Accept-Language": "zh-CN,zh;q=0.9",
            "Referer": "https://so.toutiao.com/",
        }
        params = {"keyword": query, "pd": "information"}
        try:
            async with httpx.AsyncClient(
                timeout=config.SEARCH_TIMEOUT, follow_redirects=True, headers=headers
            ) as client:
                resp = await client.get("https://so.toutiao.com/search", params=params)
        except Exception:
            return []
        if resp.status_code != 200:
            return []
        resp.encoding = "utf-8"
        return self._parse(resp.text, max_results)

    def _parse(self, html: str, max_results: int) -> List[dict]:
        soup = BeautifulSoup(html, "lxml")
        results: List[dict] = []
        # 头条结果卡片：div.result-content（含 class 含 result 的 div）
        seen_urls = set()
        for div in soup.select("div[class*='result']"):
            if "result-content" not in (div.get("class") or []):
                continue
            a = div.find("a", href=True)
            if not a:
                continue
            href = a["href"]
            if not href or href.startswith("javascript"):
                continue
            # 头条搜索结果是 /search/jump? 跳转链；保留它让浏览器跟随重定向
            if href.startswith("/"):
                href = "https://so.toutiao.com" + href
            if href in seen_urls:
                continue
            seen_urls.add(href)
            title = a.get_text(strip=True)
            if not title or len(title) < 4:
                continue
            # 摘要：可能在 div.result-desc 或 p 中
            cap = div.select_one(".result-desc, .result-content-desc, p")
            snippet = cap.get_text(strip=True) if cap else ""
            # 来源：来自 .result-footer 或 .src
            src_el = div.select_one(".result-footer, .src, .source")
            src = src_el.get_text(strip=True) if src_el else ""
            if src and snippet:
                snippet = f"{snippet} · {src}"
            elif src:
                snippet = src
            results.append({
                "title": title,
                "url": href,
                "snippet": snippet[:300],
            })
            if len(results) >= max_results:
                break
        return results
