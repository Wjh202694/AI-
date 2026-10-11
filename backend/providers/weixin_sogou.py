# -*- coding: utf-8 -*-
"""微信搜一搜（weixin.sogou.com，免密钥，公众号文章搜索）。

⚠️ 注意事项：
- 搜狗微信搜结果链接为 /link?url=<加密>，不能直接 base64 解码（加密而非编码）
- 此处保留 sogou 跳转链作为 URL，用户点开后浏览器自动跟随重定向到真实公众号文章
- 这是合规做法（搜索结果本身是 sogou 提供的中转页）
"""

from typing import List

import httpx
from bs4 import BeautifulSoup

from .base import SearchProvider
from .. import config


class WeixinSogouProvider(SearchProvider):
    name = "weixin"

    async def search(self, query: str, max_results: int = 8) -> List[dict]:
        headers = {
            "User-Agent": config.DESKTOP_UA,
            "Accept-Language": "zh-CN,zh;q=0.9",
            "Referer": "https://weixin.sogou.com/",
        }
        params = {"query": query, "type": 2}  # type=2 是文章
        try:
            async with httpx.AsyncClient(
                timeout=config.SEARCH_TIMEOUT, follow_redirects=True, headers=headers
            ) as client:
                resp = await client.get("https://weixin.sogou.com/weixin", params=params)
        except Exception:
            return []
        if resp.status_code != 200:
            return []
        resp.encoding = "utf-8"
        return self._parse(resp.text, max_results)

    def _parse(self, html: str, max_results: int) -> List[dict]:
        soup = BeautifulSoup(html, "lxml")
        results: List[dict] = []
        # 每个结果是 ul li（带 d 属性）
        for li in soup.select("li[uigs], li.news-list, div.news-box"):
            h3 = li.find("h3")
            a = h3.find("a") if h3 else None
            if not a or not a.get("href"):
                continue
            # 保留 sogou 跳转链（用户点开后浏览器跟随重定向）
            href = a["href"]
            if href.startswith("/"):
                href = "https://weixin.sogou.com" + href
            title = a.get_text(strip=True)
            # 摘要：p.txt-info 或 .txt-info
            cap = li.select_one("p.txt-info, .txt-info")
            snippet = cap.get_text(strip=True) if cap else ""
            # 公众号名：span.all-time-y2 或 a.np
            from_label = li.select_one("span.all-time-y2, a.np, .account")
            from_name = from_label.get_text(strip=True) if from_label else ""
            results.append({
                "title": f"{title}（{from_name}）" if from_name else title,
                "url": href,
                "snippet": snippet[:300],
            })
            if len(results) >= max_results:
                break
        return results
