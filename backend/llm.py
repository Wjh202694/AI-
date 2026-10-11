# -*- coding: utf-8 -*-
"""可选 LLM 增强：把用户问题改写成一条更贴近意图的检索式。

默认关闭——需通过环境变量配置 OpenAI 兼容端点（未配置则 is_configured()=False，
enhance() 返回 None，前端自动降级为纯规则）。这与「规则为主·LLM 可开」的产品定位一致。
"""

import os
import httpx
from typing import List, Optional

BASE = os.getenv("SOUYI_LLM_BASE", "").strip()
KEY = os.getenv("SOUYI_LLM_KEY", "").strip()
MODEL = os.getenv("SOUYI_LLM_MODEL", "gpt-4o-mini").strip()


def is_configured() -> bool:
    return bool(BASE and KEY)


_SYSTEM = (
    "你是一个检索式改写助手。用户会给你一个模糊的中文问题，以及已从问题中拆出的关键词。"
    "请只输出一条最贴近用户真实意图、可直接用于搜索引擎的高级检索式"
    "（可合理使用 site: / filetype: / 引号 / 减号 等语法，但不要滥用）。"
    "不要解释、不要换行、不要使用 Markdown，只输出检索式本身。"
)


async def enhance(question: str, terms: List[str]) -> Optional[str]:
    """返回 LLM 改写后的推荐检索式；任何异常都返回 None（交由前端降级）。"""
    if not is_configured():
        return None
    user = f"问题：{question}\n已拆关键词：{('、'.join(terms)) if terms else '（无）'}"
    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.post(
                BASE.rstrip("/") + "/chat/completions",
                headers={"Authorization": f"Bearer {KEY}", "Content-Type": "application/json"},
                json={
                    "model": MODEL,
                    "messages": [
                        {"role": "system", "content": _SYSTEM},
                        {"role": "user", "content": user},
                    ],
                    "temperature": 0.3,
                    "max_tokens": 120,
                },
            )
            resp.raise_for_status()
            data = resp.json()
            q = data["choices"][0]["message"]["content"].strip()
            # 去 Markdown 代码围栏等可能残留
            q = q.strip("`").strip()
            return q or None
    except Exception:
        return None
