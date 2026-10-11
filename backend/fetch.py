# -*- coding: utf-8 -*-
"""抓取正文 + 内容相关度多维度判定。

硬过滤规则（任一不满足则视为不相关，结果丢弃）：
1. 抓得到正文
2. 正文长度 ≥ MIN_BODY_CHARS（避免导航页误判）
3. 至少 1 个核心词出现在标题里（标题无关 = 主题必不相关）
4. 至少 1 个核心词出现在前 N 段（前 N 段无关 = 开头不切入主题）
5. 链接密度 ≤ MAX_LINK_DENSITY（避免导航页/链接目录）
6. 句子命中率 ≥ MIN_HIT_RATIO

放宽阈值（relaxe 后）：
- 只保留 ①②③④⑤，命中率门槛降到 RELAX_HIT_RATIO
- 并打上「边缘相关」标签，UI 提示用户人工核验
"""

import asyncio
import re
from typing import List, Optional, Tuple
from urllib.parse import urlparse

import httpx
from bs4 import BeautifulSoup

from . import config

# 噪声标签：完全剥离（连同内容一起删）
_NOISE_TAGS = ["script", "style", "noscript", "iframe", "header", "footer",
               "nav", "aside", "form", "button", "svg", "canvas"]

# 内容提取优先级：第一个匹配上的优先用
_CONTENT_SELECTORS = [
    "article",
    "main",
    "[role='main']",
    ".article-content",
    ".post-content",
    ".entry-content",
    "#content",
    "#article",
    "body",
]

# 中文分句边界（句号、问号、感叹号、分号、双换行）
_SENT_SPLIT_RE = re.compile(r"(?<=[。！？；\?])\s*|\n{2,}")

# 空白归一化
_WS_RE = re.compile(r"\s+")


# 多维度阈值常量
MIN_BODY_CHARS = 100           # 正文长度下限（放宽：很多页面正文被导航、推荐项稀释）
HEAD_PARAGRAPH_COUNT = 3       # "前 N 段" 的 N
# 链接密度判定已移除：中文网页导航菜单本身使链接占比高，误判严重。
HIT_SAMPLE = 30                # 命中率采样句数（前 N 句）
MIN_HIT_COUNT = 2              # 采样区内核心词至少出现 N 次才算“有明确提及”


def _is_fetchable_url(url: str) -> bool:
    """二进制 / 非 HTML 直接判 false，避免抓回来当文本算。"""
    if not url:
        return False
    p = urlparse(url)
    if p.scheme not in ("http", "https"):
        return False
    path = (p.path or "").lower()
    if path.endswith((".pdf", ".doc", ".docx", ".xls", ".xlsx",
                       ".ppt", ".pptx", ".zip", ".rar", ".7z",
                       ".jpg", ".jpeg", ".png", ".gif", ".webp", ".mp4")):
        return False
    return True


async def fetch_text(url: str, timeout: float = None) -> Optional[str]:
    """抓取 URL 文本内容（剥离噪声标签）；失败或非 HTML 返回 None。"""
    if not _is_fetchable_url(url):
        return None
    t = timeout if timeout is not None else config.FETCH_TIMEOUT
    headers = {"User-Agent": config.DESKTOP_UA,
               "Accept": "text/html,application/xhtml+xml;q=0.9,*/*;q=0.8",
               "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8"}
    try:
        async with httpx.AsyncClient(timeout=t, follow_redirects=True,
                                      headers=headers) as client:
            resp = await client.get(url)
            if resp.status_code >= 400:
                return None
            ctype = resp.headers.get("content-type", "").lower()
            if ctype and "html" not in ctype and "xml" not in ctype and "text" not in ctype:
                return None
            if len(resp.content) > config.FETCH_MAX_BYTES:
                return None
            html = resp.text
    except Exception:
        return None

    return _extract_text(html)


def _extract_text(html: str) -> Optional[str]:
    """HTML → 纯文本（去噪声标签 + 优先取 article/main）。"""
    try:
        soup = BeautifulSoup(html, "lxml")
    except Exception:
        return None
    for tag in _NOISE_TAGS:
        for el in soup.find_all(tag):
            el.decompose()
    target = None
    for sel in _CONTENT_SELECTORS:
        try:
            target = soup.select_one(sel)
        except Exception:
            target = None
        if target:
            break
    if target is None:
        return None
    text = target.get_text(separator=" ", strip=True)
    text = _WS_RE.sub(" ", text).strip()
    return text or None


def split_sentences(text: str) -> List[str]:
    """中文分句；过滤 < MIN_SENTENCE_CHARS 的短句。"""
    if not text:
        return []
    normalized = text.replace("\r\n", "\n")
    raw = _SENT_SPLIT_RE.split(normalized)
    out = []
    for s in raw:
        s = s.strip()
        if len(s) >= config.MIN_SENTENCE_CHARS:
            out.append(s)
    return out


def hit_ratio(text: str, terms: List[str], max_sentences: int = HIT_SAMPLE) -> Tuple[float, int, int]:
    """返回 (命中率, 命中句数, 总句数)。

    分母限到前 max_sentences 句（默认 30），避免长文被稀释。
    """
    sentences = split_sentences(text)
    sample = sentences[:max_sentences]
    total = len(sample)
    if total == 0:
        return 0.0, 0, 0
    if not terms:
        return 0.0, 0, total
    keys = [t for t in terms if t and t.strip()]
    if not keys:
        return 0.0, 0, total
    hit = 0
    for s in sample:
        if any(k in s for k in keys):
            hit += 1
    return hit / total, hit, total


def hit_count(text: str, terms: List[str], max_sentences: int = HIT_SAMPLE) -> int:
    """返回前 N 句中“含核心词的句子数”。可作为命中率的补充。"""
    sentences = split_sentences(text)[:max_sentences]
    if not terms:
        return 0
    keys = [t for t in terms if t and t.strip()]
    if not keys:
        return 0
    return sum(1 for s in sentences if any(k in s for k in keys))


def _link_density(text: str, html: str) -> float:
    """估算「外链字符占比」：a 标签文本中指向外部的真实链接（href 以 http 开头且不同域）的字符占比。

    返回比例 0.0~1.0。> 0.5 视为导航/链接目录页。
    """
    if not html or not text:
        return 0.0
    try:
        soup = BeautifulSoup(html, "lxml")
    except Exception:
        return 0.0
    seen_texts = set()
    link_chars = 0
    for a in soup.find_all("a"):
        href = a.get("href", "") or ""
        # 只算外链（http/https 开头且不是本页面 /空 /锚点 /js）
        if not href.startswith("http"):
            continue
        t = a.get_text(strip=True)
        if not t or t in seen_texts:
            continue
        seen_texts.add(t)
        link_chars += len(t)
    total = max(len(text), 1)
    return min(1.0, link_chars / total)


def _has_term_in_head(text: str, terms: List[str], n_paragraphs: int = HEAD_PARAGRAPH_COUNT) -> bool:
    """正文前 N 段是否包含至少一个核心词。段落按双换行切。"""
    if not terms or not text:
        return False
    paras = [p.strip() for p in re.split(r"\n{2,}", text) if p.strip()]
    head = " ".join(paras[:n_paragraphs])
    return any(t in head for t in terms if t and t.strip())


def _has_term_in_title(title: str, terms: List[str]) -> bool:
    """标题里是否含至少一个核心词。"""
    if not title or not terms:
        return False
    return any(t in title for t in terms if t and t.strip())


def assess(html: str, text: str, title: str, terms: List[str],
           threshold: float = None) -> dict:
    """对一条结果做多维度内容相关度评估。

    返回 dict：
    - passed: bool — 是否通过硬过滤
    - relevance: str — "high" | "relaxed" | "low"
    - reasons: List[str] — 通过/不通过的维度明细（用于溯源）
    - ratio, hit, total, body_chars, link_density
    """
    threshold = threshold if threshold is not None else config.MIN_HIT_RATIO
    body_chars = len(text or "")
    ratio, hit, total = hit_ratio(text or "", terms or [])
    density = _link_density(text or "", html or "")
    title_ok = _has_term_in_title(title or "", terms or [])
    head_ok = _has_term_in_head(text or "", terms or [])

    reasons = []
    passed = True

    if body_chars < MIN_BODY_CHARS:
        reasons.append(f"正文过短({body_chars}字)")
        passed = False
    else:
        reasons.append(f"正文{body_chars}字")

    # 标题 + 前 3 段任一含核心词即过（标题可能不含但开头含）
    if not title_ok and not head_ok:
        reasons.append("标题与前3段均无核心词")
        passed = False
    elif title_ok:
        reasons.append("标题含核心词")
    else:
        reasons.append("前3段含核心词（标题未含）")

    if total == 0:
        reasons.append("分句后无有效句")
        passed = False
    elif ratio >= threshold:
        reasons.append(f"命中{ratio:.0%}({hit}/{total})≥{threshold:.0%}")
    elif threshold < config.MIN_HIT_RATIO and hit >= MIN_HIT_COUNT:
        # 放宽模式 + 绝对命中数足够：保留但打"边缘"标签
        reasons.append(f"命中{ratio:.0%}({hit}/{total})≥{MIN_HIT_COUNT}次，边缘相关")
    else:
        reasons.append(f"命中{ratio:.0%}({hit}/{total})<{threshold:.0%}")
        passed = False

    # relevance 分级
    if not passed:
        relevance = "low"
    elif ratio >= config.MIN_HIT_RATIO:
        relevance = "high"
    else:
        relevance = "relaxed"

    return {
        "passed": passed,
        "relevance": relevance,
        "reasons": reasons,
        "ratio": ratio,
        "hit": hit,
        "total": total,
        "body_chars": body_chars,
        "link_density": density,
    }


async def fetch_many_with_meta(urls: List[str]) -> List[Tuple[Optional[str], Optional[str]]]:
    """并发抓取多条 (html, text)；失败位置 (None, None)。

    同时返回 html 是为了做链接密度判定。
    """
    sem = asyncio.Semaphore(config.FETCH_CONCURRENCY)

    async def _one(url: str) -> Tuple[Optional[str], Optional[str]]:
        async with sem:
            if not _is_fetchable_url(url):
                return None, None
            t = config.FETCH_TIMEOUT
            headers = {"User-Agent": config.DESKTOP_UA,
                       "Accept": "text/html,application/xhtml+xml;q=0.9,*/*;q=0.8",
                       "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8"}
            try:
                async with httpx.AsyncClient(timeout=t, follow_redirects=True,
                                              headers=headers) as client:
                    resp = await client.get(url)
                    if resp.status_code >= 400:
                        return None, None
                    ctype = resp.headers.get("content-type", "").lower()
                    if ctype and "html" not in ctype and "xml" not in ctype and "text" not in ctype:
                        return None, None
                    if len(resp.content) > config.FETCH_MAX_BYTES:
                        return None, None
                    html = resp.text
            except Exception:
                return None, None
            text = _extract_text(html)
            return html, text

    return await asyncio.gather(*[_one(u) for u in urls])


async def fetch_many(urls: List[str]) -> List[Optional[str]]:
    """兼容旧接口：只返回 text。"""
    pairs = await fetch_many_with_meta(urls)
    return [t for (_, t) in pairs]


def passes_filter(text: str, terms: List[str], threshold: float = None) -> bool:
    """便捷判定：是否达到阈值。threshold 默认 config.MIN_HIT_RATIO。"""
    t = threshold if threshold is not None else config.MIN_HIT_RATIO
    r, _, _ = hit_ratio(text, terms)
    return r >= t
