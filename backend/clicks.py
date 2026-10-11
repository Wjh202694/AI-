# -*- coding: utf-8 -*-
"""用户点击量：按 URL 全局累积。

- 数据表 clicks(url TEXT PRIMARY KEY, count INTEGER DEFAULT 0)
- POST /api/click {url} → UPSERT count = count + 1
- aggregate() 调用 get_counts(urls) 取批量点击数用于排序
"""

import sqlite3
from typing import Dict, Iterable, List

from . import config

_SCHEMA = """
CREATE TABLE IF NOT EXISTS clicks (
  url TEXT PRIMARY KEY,
  count INTEGER NOT NULL DEFAULT 0
);
"""


def _conn() -> sqlite3.Connection:
    config.DATA_DIR.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(config.DB_PATH))
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    with _conn() as conn:
        conn.executescript(_SCHEMA)


def record_click(url: str) -> int:
    """一次点击：count + 1，返回当前累计值。"""
    if not url:
        return 0
    init_db()
    with _conn() as conn:
        conn.execute(
            "INSERT INTO clicks(url, count) VALUES(?, 1) "
            "ON CONFLICT(url) DO UPDATE SET count = count + 1",
            (url,))
        row = conn.execute("SELECT count FROM clicks WHERE url=?", (url,)).fetchone()
    return int(row["count"]) if row else 0


def get_counts(urls: Iterable[str]) -> Dict[str, int]:
    """批量读取点击数；未点过的 URL 不在返回字典里（默认 0）。"""
    urls = [u for u in urls if u]
    if not urls:
        return {}
    init_db()
    placeholders = ",".join("?" * len(urls))
    with _conn() as conn:
        rows = conn.execute(
            f"SELECT url, count FROM clicks WHERE url IN ({placeholders})",
            urls).fetchall()
    return {r["url"]: int(r["count"]) for r in rows}


def top_urls(limit: int = 20) -> List[dict]:
    """历史最热门 URL（调试 / 未来扩展用）。"""
    init_db()
    with _conn() as conn:
        rows = conn.execute(
            "SELECT url, count FROM clicks ORDER BY count DESC, url LIMIT ?",
            (limit,)).fetchall()
    return [dict(r) for r in rows]
