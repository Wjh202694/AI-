# -*- coding: utf-8 -*-
"""Bing 主通道（cn.bing.com，免密钥）。

要点：
- 桌面 UA + mkt=zh-CN + Accept-Language，防反爬；
- 结果链接多为 bing.com/ck/a?...&u=a1<base64> 跳转链，必须还原真实 URL（溯源命门）；
- 解析为空视为被反爬，抛 ProviderBlocked 供上层切备用通道。
"""

import base64
import re
from typing import List
from urllib.parse import urlparse, parse_qs

import httpx
from bs4 import BeautifulSoup

from .base import SearchProvider
from .. import config


class ProviderBlocked(Exception):
    """通道被反爬/封禁，上层应切换备用通道。"""


def restore_bing_url(href: str) -> str:
    """把 bing.com/ck/a 跳转链还原为真实目标 URL。"""
    if not href:
        return href
    if "bing.com/ck/a" not in href:
        return href
    try:
        qs = parse_qs(urlparse(href).query)
        u = qs.get("u", [""])[0]
        if u.startswith("a1"):
            payload = u[2:]
            # base64url 补位
            payload += "=" * (-len(payload) % 4)
            return base64.urlsafe_b64decode(payload).decode("utf-8", "ignore")
    except Exception:
        pass
    return href


class BingProvider(SearchProvider):
    name = "bing"

    async def search(self, query: str, max_results: int = 8) -> List[dict]:
        headers = {
            "User-Agent": config.DESKTOP_UA,
            "Accept-Language": "zh-CN,zh;q=0.9",
        }
        params = {"q": query, "mkt": "zh-CN", "setlang": "zh-CN", "count": str(max_results)}
        async with httpx.AsyncClient(
            timeout=config.SEARCH_TIMEOUT, follow_redirects=True, headers=headers
        ) as client:
            resp = await client.get("https://www.bing.com/search", params=params)
        if resp.status_code in (403, 429):
            raise ProviderBlocked(f"Bing 返回 {resp.status_code}")
        resp.encoding = "utf-8"
        return self._parse(resp.text, max_results)

    def _parse(self, html: str, max_results: int) -> List[dict]:
        soup = BeautifulSoup(html, "lxml")
        results: List[dict] = []
        for li in soup.select("li.b_algo"):
            h2 = li.find("h2")
            a = h2.find("a") if h2 else None
            if not a or not a.get("href"):
                continue
            url = restore_bing_url(a["href"])
            title = a.get_text(strip=True)
            cap = li.select_one(".b_caption p") or li.find("p")
            snippet = cap.get_text(strip=True) if cap else ""
            results.append({"title": title, "url": url, "snippet": snippet[:300]})
            if len(results) >= max_results:
                break
        if not results:
            # 有验证码/异常页特征则判定位反爬
            if re.search(r"b_captcha|verify|captcha", html, re.I):
                raise ProviderBlocked("Bing 触发验证码")
            raise ProviderBlocked("Bing 解析结果为空（疑似反爬或页面结构变更）")
        return results
