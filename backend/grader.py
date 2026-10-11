# -*- coding: utf-8 -*-
"""一手/二手分级：域名三层表 + 规则打分（0-100）。

2026-10-06 增强（回应 design review F1/F2 + 用户约束）：
- 时间维度：语料含年份且距今超过 STALE_YEARS 年 → 标 stale，判为「可能的一手资料」并提醒核对最新数据
- 溯源说明：返回 provenance_note，解释「为何判此级」（文章灵魂：可溯源）
- 官方直达：channel=="site"（一手站点）标记 is_official_deep，UI 提示「官方直达资料页」
"""

import re
from datetime import datetime
from urllib.parse import urlparse

from . import config

GRADE_LABELS = {
    "primary": "一手·可下结论",
    "unsure": "存疑·需交叉验证",
    "secondary": "二手·仅找线索",
}
STALE_LABEL = "可能一手·年代较久"
STALE_YEARS = 3

_YEAR_RE = re.compile(r"(?:19|20)\d{2}")


def extract_domain(url: str) -> str:
    try:
        host = urlparse(url).netloc.lower()
        return host[4:] if host.startswith("www.") else host
    except Exception:
        return ""


def _domain_matches(domain: str, patterns) -> bool:
    for p in patterns:
        p = p.lower()
        if domain == p or domain.endswith("." + p) or domain.endswith(p):
            return True
    return False


def _extract_year(text: str):
    """从标题/链接/摘要里取最近的一个 4 位年份作为文档年份。"""
    yrs = [int(y) for y in _YEAR_RE.findall(text or "")]
    return max(yrs) if yrs else None


def _build_provenance(grade, domain, is_pdf, hits, stale, channel):
    parts = []
    if channel == "site":
        parts.append("一手站点官方信息披露原文，已直达资料页")
    elif domain and _domain_matches(domain, config.PRIMARY_DOMAINS):
        parts.append(f"来源为官方/权威域名（{domain}），属一手来源")
    elif domain and _domain_matches(domain, config.SECONDARY_DOMAINS):
        parts.append(f"来源为自媒体/内容平台（{domain}），属二手转述")
    if is_pdf:
        parts.append("且为 PDF/原始文件")
    if hits:
        parts.append("命中一手信号词")
    if not parts:
        if grade == "primary":
            parts.append("综合多信号判定为一手")
        elif grade == "secondary":
            parts.append("综合信号偏低，判为二手")
        else:
            parts.append("来源不明确，需交叉验证")
    if stale:
        parts.append(f"距今年限超过 {STALE_YEARS} 年，判为「可能的一手资料」，建议核对最新数据")
    return " · ".join(parts)


def grade_result(title: str, url: str, snippet: str = "", channel: str = "web") -> dict:
    """对单条结果打分分级，返回完整分级结论。"""
    domain = extract_domain(url)
    text = (title or "") + " " + (url or "") + " " + (snippet or "")
    score = 50.0
    grade = None

    # 域名层级 ±40
    if domain and _domain_matches(domain, config.PRIMARY_DOMAINS):
        score += 40
        grade = "primary"
    elif domain and _domain_matches(domain, config.SECONDARY_DOMAINS):
        score -= 25
        grade = "secondary"

    # 一手弱信号 +20（累计封顶）
    hits = sum(1 for w in config.PRIMARY_HINT_WORDS if w in text)
    score += min(hits * 7, 20)

    # PDF/官方文档 +10
    is_pdf = url.lower().endswith(".pdf") or "filetype:pdf" in url.lower()
    if is_pdf:
        score += 10

    # 年份信号：近期 +5；过久则标 stale
    doc_year = _extract_year(text)
    stale = False
    if doc_year:
        age = datetime.now().year - doc_year
        if 0 <= age <= 1:
            score += 5
        elif age > STALE_YEARS:
            stale = True

    # 内容农场 −15
    if any(w in (title or "") for w in config.CONTENT_FARM_WORDS):
        score -= 15

    score = max(0.0, min(100.0, score))

    if grade is None:
        if score >= 70:
            grade = "primary"
        elif score < 40:
            grade = "secondary"
        else:
            grade = "unsure"
    else:
        if grade == "primary" and score < 55:
            grade = "unsure"
        elif grade == "secondary" and score > 75:
            grade = "unsure"

    # 年代过久的一手 → 降级标注为「可能的一手资料」
    grade_label = GRADE_LABELS[grade]
    if stale and grade == "primary":
        grade_label = STALE_LABEL

    provenance_note = _build_provenance(grade, domain, is_pdf, hits, stale, channel)

    return {
        "grade": grade,
        "grade_label": grade_label,
        "score": round(score, 1),
        "domain": domain,
        "provenance_note": provenance_note,
        "stale": stale,
        "is_official_deep": channel == "site",
    }
