# -*- coding: utf-8 -*-
"""OpenAlex 学术论文元数据（api.openalex.org，免费 200k/天）。

OpenAlex 是覆盖 2 亿+ 学术成果的开放索引，比 Google Scholar 反爬松、比 Web of Science 开放。
适合学术类查询（论文、综述、研究报告）。
"""

from typing import List

import httpx

from .base import SearchProvider
from .. import config


class OpenAlexProvider(SearchProvider):
    name = "openalex"

    async def search(self, query: str, max_results: int = 8) -> List[dict]:
        # OpenAlex 要求带上 User-Agent（含联系方式），否则可能被限流
        mailto = "souyi-contact@example.com"  # 可改为真实邮箱以提升速率
        params = {
            "search": query,
            "per_page": str(max_results),
            "mailto": mailto,
        }
        headers = {"User-Agent": f"Souyi/1.0 (mailto:{mailto})"}
        try:
            async with httpx.AsyncClient(
                timeout=config.SEARCH_TIMEOUT, follow_redirects=True, headers=headers
            ) as client:
                resp = await client.get("https://api.openalex.org/works", params=params)
        except Exception:
            return []
        if resp.status_code != 200:
            return []
        try:
            data = resp.json()
        except Exception:
            return []
        results: List[dict] = []
        for w in data.get("results", [])[:max_results]:
            # 标题可能是 None（OpenAlex 偶尔会缺失）
            title = (w.get("title") or w.get("display_name") or "").strip()
            if not title:
                continue
            url = w.get("doi") or w.get("id") or ""
            # 把 doi 链接标准化为可访问 URL
            if url.startswith("https://openalex.org/"):
                doi_url = w.get("doi") or ""
                if doi_url.startswith("https://doi.org/"):
                    url = doi_url
            elif url.startswith("http"):
                pass
            else:
                url = ""
            # 摘要：abstract_inverted_index 是 OpenAlex 倒排索引格式，反转为文本
            abstract = _reconstruct_abstract(w.get("abstract_inverted_index"))
            # 作者
            authorships = w.get("authorships") or []
            author_names = []
            for au in authorships[:3]:
                author = au.get("author", {})
                name = author.get("display_name")
                if name:
                    author_names.append(name)
            author_str = "、".join(author_names) if author_names else ""
            # 发表年份
            year = w.get("publication_year")
            year_str = f" ({year})" if year else ""
            # 期刊/来源
            host = w.get("primary_location", {}) or {}
            src = (host.get("source") or {}).get("display_name") if isinstance(host.get("source"), dict) else ""
            snippet_parts = []
            if author_str:
                snippet_parts.append(f"作者：{author_str}")
            if src:
                snippet_parts.append(f"来源：{src}")
            if abstract:
                snippet_parts.append(abstract[:240])
            snippet = " · ".join(snippet_parts)
            full_title = f"{title}{year_str}"
            results.append({
                "title": full_title,
                "url": url,
                "snippet": snippet[:300],
            })
        return results


def _reconstruct_abstract(inverted_index) -> str:
    """OpenAlex 把摘要存为倒排索引 {word: [pos1, pos2, ...]}，反转为可读文本。"""
    if not inverted_index or not isinstance(inverted_index, dict):
        return ""
    # 找到最大位置，决定数组长度
    max_pos = 0
    for positions in inverted_index.values():
        if positions:
            max_pos = max(max_pos, max(positions))
    if max_pos == 0:
        return ""
    words = [""] * (max_pos + 1)
    for word, positions in inverted_index.items():
        for p in positions:
            if 0 <= p <= max_pos:
                words[p] = word
    return " ".join(w for w in words if w).strip()
