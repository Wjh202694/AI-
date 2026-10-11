# -*- coding: utf-8 -*-
"""GitHub 仓库 / 代码搜索 API（api.github.com/search/repositories）。

适合"怎么做 / 实现 / 代码示例"类查询——拿到开源代码仓库。
未鉴权：60 次/小时；带 token：5000 次/小时。
"""

from typing import List

import httpx

from .base import SearchProvider
from .. import config


class GitHubProvider(SearchProvider):
    name = "github"

    async def search(self, query: str, max_results: int = 6) -> List[dict]:
        params = {"q": query, "per_page": str(max_results), "sort": "stars", "order": "desc"}
        headers = {
            "Accept": "application/vnd.github.v3+json",
            "User-Agent": "Souyi-Search/1.0",
        }
        # 可选：环境变量 GITHUB_TOKEN 可提升速率
        import os
        token = os.getenv("SOUYI_GITHUB_TOKEN", "").strip()
        if token:
            headers["Authorization"] = f"Bearer {token}"
        try:
            async with httpx.AsyncClient(
                timeout=config.SEARCH_TIMEOUT, follow_redirects=True, headers=headers
            ) as client:
                resp = await client.get("https://api.github.com/search/repositories",
                                         params=params)
        except Exception:
            return []
        if resp.status_code != 200:
            return []
        try:
            data = resp.json()
        except Exception:
            return []
        results: List[dict] = []
        for repo in data.get("items", [])[:max_results]:
            full_name = repo.get("full_name", "")
            html_url = repo.get("html_url", "")
            description = (repo.get("description") or "").strip()
            stars = repo.get("stargazers_count", 0)
            language = repo.get("language") or ""
            updated = repo.get("updated_at", "")[:10]
            title = full_name or repo.get("name", "")
            snippet_parts = []
            if description:
                snippet_parts.append(description)
            meta = []
            if language:
                meta.append(language)
            if stars:
                meta.append(f"⭐{stars}")
            if updated:
                meta.append(f"更新 {updated}")
            if meta:
                snippet_parts.append(" · ".join(meta))
            results.append({
                "title": title,
                "url": html_url,
                "snippet": "  ".join(snippet_parts)[:300],
            })
        return results
