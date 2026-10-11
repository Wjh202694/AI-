# -*- coding: utf-8 -*-
"""搜索历史：SQLite 存储，回看 / 重新执行 / 导出 Markdown。"""

import json
import sqlite3
from datetime import datetime
from typing import List, Optional

from . import config

_SCHEMA = """
CREATE TABLE IF NOT EXISTS searches (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  question TEXT NOT NULL,
  query_matrix TEXT NOT NULL,
  created_at TEXT NOT NULL,
  llm_used INTEGER DEFAULT 0,
  result_count INTEGER DEFAULT 0
);
CREATE TABLE IF NOT EXISTS results (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  search_id INTEGER NOT NULL REFERENCES searches(id) ON DELETE CASCADE,
  channel TEXT NOT NULL,
  grade TEXT NOT NULL,
  title TEXT, url TEXT, snippet TEXT,
  score REAL, rank INTEGER,
  is_counter INTEGER DEFAULT 0,
  source_query TEXT DEFAULT '',
  provenance_note TEXT DEFAULT '',
  stale INTEGER DEFAULT 0,
  is_official_deep INTEGER DEFAULT 0,
  relevance TEXT DEFAULT 'high',
  relevance_reasons TEXT DEFAULT ''
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
        # 增量迁移：老库补列（ADD COLUMN 重复会报错，逐个吞掉）
        for col in ("provenance_note TEXT DEFAULT ''", "stale INTEGER DEFAULT 0",
                    "is_official_deep INTEGER DEFAULT 0",
                    "relevance TEXT DEFAULT 'high'",
                    "relevance_reasons TEXT DEFAULT ''"):
            try:
                conn.execute(f"ALTER TABLE results ADD COLUMN {col}")
            except sqlite3.OperationalError:
                pass


def save_search(question: str, queries: list, results: list, llm_used: bool) -> int:
    init_db()
    matrix = json.dumps([q.dict() for q in queries], ensure_ascii=False)
    with _conn() as conn:
        cur = conn.execute(
            "INSERT INTO searches(question, query_matrix, created_at, llm_used, result_count) "
            "VALUES (?,?,?,?,?)",
            (question, matrix, datetime.now().isoformat(timespec="seconds"),
             1 if llm_used else 0, len(results)))
        sid = cur.lastrowid
        for rank, r in enumerate(results):
            conn.execute(
                "INSERT INTO results(search_id, channel, grade, title, url, snippet, score, rank, "
                "is_counter, source_query, provenance_note, stale, is_official_deep, "
                "relevance, relevance_reasons) "
                "VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
                (sid, r.channel, r.grade, r.title, r.url, r.snippet, r.score, rank,
                 1 if r.is_counter else 0, r.source_query,
                 getattr(r, "provenance_note", "") or "",
                 1 if getattr(r, "stale", False) else 0,
                 1 if getattr(r, "is_official_deep", False) else 0,
                 getattr(r, "relevance", "high") or "high",
                 getattr(r, "relevance_reasons", "") or ""))
    return sid


def list_searches(limit: int = 50) -> List[dict]:
    init_db()
    with _conn() as conn:
        rows = conn.execute(
            "SELECT id, question, created_at, result_count, llm_used FROM searches "
            "ORDER BY id DESC LIMIT ?", (limit,)).fetchall()
    return [dict(r) for r in rows]


def get_search(search_id: int) -> Optional[dict]:
    init_db()
    with _conn() as conn:
        s = conn.execute("SELECT * FROM searches WHERE id=?", (search_id,)).fetchone()
        if not s:
            return None
        rs = conn.execute(
            "SELECT * FROM results WHERE search_id=? ORDER BY rank", (search_id,)).fetchall()
    return {
        "id": s["id"], "question": s["question"], "created_at": s["created_at"],
        "query_matrix": json.loads(s["query_matrix"]),
        "llm_used": bool(s["llm_used"]),
        "results": [dict(r) for r in rs],
    }


def export_markdown(search_id: int) -> Optional[str]:
    data = get_search(search_id)
    if not data:
        return None
    lines = [
        f"# 搜索记录：{data['question']}",
        f"",
        f"- 时间：{data['created_at']}",
        f"- 检索编号：{search_id}",
        f"",
        f"## 执行的查询",
    ]
    for q in data["query_matrix"]:
        mark = "x" if q.get("checked") else " "
        lines.append(f"- [{mark}] 【{q['group_name']}】`{q['query']}`")
    lines.append("")

    groups = [
        ("primary", "一手资料（可下结论）"),
        ("unsure", "存疑待核（需交叉验证）"),
        ("secondary", "二手线索（仅作参考）"),
    ]
    counter = [r for r in data["results"] if r.get("is_counter")]

    for grade, title in groups:
        rs = [r for r in data["results"]
              if r["grade"] == grade and not r.get("is_counter")]
        if not rs:
            continue
        lines.append(f"## {title}")
        for r in rs:
            lines.append(f"- [{r['title']}]({r['url']})")
            if r.get("snippet"):
                lines.append(f"  - {r['snippet'][:150]}")
            if r.get("provenance_note"):
                lines.append(f"  - 溯源：{r['provenance_note']}")
        lines.append("")

    if counter:
        lines.append("## 反面搜索结果")
        for r in counter:
            lines.append(f"- [{r['title']}]({r['url']})")
            if r.get("provenance_note"):
                lines.append(f"  - 溯源：{r['provenance_note']}")
        lines.append("")

    lines.append("---")
    lines.append("溯源原则：一手资料用来下结论，二手转述用来找线索，别人的观点只用来做参考。")
    return "\n".join(lines)
