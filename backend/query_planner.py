# -*- coding: utf-8 -*-
"""规则拆词 + 查询矩阵生成（纯离线，LLM 扩展词由前端传入后合并）。"""

import re
from datetime import datetime
from typing import Dict, List, Tuple

from . import config
from .models import QueryItem


def extract_terms(question: str, extra_terms: List[str] = None) -> Tuple[List[str], List[str]]:
    """从问句中拆出关键词，并命中行业黑话映射。

    返回 (关键词列表, 黑话扩展列表)。
    """
    text = question.strip()
    # 按标点/空白切分
    raw_tokens = [t for t in re.split(r"[\s，。！？；：、,.!?;:\"'“”‘’（）()【】\[\]]+", text) if t]

    terms: List[str] = []
    # 先整句匹配黑话映射的键（如"考研""房价"可能嵌在长 token 里）
    jargon: List[str] = []
    hit_keys: List[str] = []
    for key, expansions in config.JARGON_MAP.items():
        if key in text:
            jargon.extend(expansions)
            hit_keys.append(key)
            if key not in terms and key not in config.STOP_WORDS:
                terms.append(key)

    for token in raw_tokens:
        # 先移除已整词命中的黑话键，避免被单字停用词切坏
        cleaned = token
        for key in hit_keys:
            cleaned = cleaned.replace(key, " ")
        # 再剥掉头尾停用虚词后看剩余部分
        for sw in sorted(config.STOP_WORDS, key=len, reverse=True):
            if len(sw) >= 2:
                cleaned = cleaned.replace(sw, " ")
        # 单字停用词只剥首尾，不切词中
        cleaned = cleaned.strip()
        for sw in sorted(config.STOP_WORDS, key=len, reverse=True):
            if len(sw) == 1:
                while cleaned.startswith(sw) and len(cleaned) > 2:
                    cleaned = cleaned[1:]
                while cleaned.endswith(sw) and len(cleaned) > 2:
                    cleaned = cleaned[:-1]
        for piece in cleaned.split():
            piece = piece.strip()
            if not piece or piece in config.STOP_WORDS:
                continue
            if len(piece) < 2 and not re.search(r"[A-Za-z0-9]", piece):
                continue
            if piece not in terms:
                terms.append(piece)

    # 合并前端 LLM 扩展词
    for t in (extra_terms or []):
        t = t.strip()
        if t and t not in terms:
            jargon.append(t)

    # 去重保序
    seen = set()
    jargon = [x for x in jargon if not (x in seen or seen.add(x))]
    return terms[:8], jargon[:8]


def build_query_matrix(question: str, terms: List[str], jargon: List[str],
                       answers: Dict[str, str] = None) -> List[QueryItem]:
    """生成五组查询矩阵 A/B/C/D/E。answers 用于据用户追问作答细化。"""
    a = answers or {}
    items: List[QueryItem] = []
    q = question.strip()

    # A 组：原始问句
    items.append(QueryItem(
        group="A", group_name="原始问句", query=q,
        note="直接搜你的原话，作为对照基线"))

    # B 组：拆词组合（2~3 条）
    core = [t for t in terms if t][:4]
    if len(core) >= 2:
        items.append(QueryItem(
            group="B", group_name="拆词组合", query=" ".join(core[:3]),
            note="拆出的核心词 AND 组合，比整句更准"))
        if len(core) >= 3:
            items.append(QueryItem(
                group="B", group_name="拆词组合", query=" ".join(core[:2]) + " 最新",
                note="加时效词，避开过时信息", checked=False))
    if jargon:
        items.append(QueryItem(
            group="B", group_name="拆词组合",
            query=" ".join((core[:2] + jargon[:2])),
            note="混入行业黑话：答案所在的地方会这么写"))

    # 时效作答：补充年份 / 历史视角查询
    time_vals = _answer_values(a, "time")
    time_v = time_vals[0] if time_vals else None
    if time_v == "recent":
        yr = datetime.now().year
        items.append(QueryItem(
            group="B", group_name="拆词组合",
            query=f"{core[0]} {yr} {yr-1} 最新",
            note=f"锁定近 2 年（{yr-1}–{yr}），过滤过时信息", checked=False))
    elif time_v == "recent2":
        yr = datetime.now().year
        items.append(QueryItem(
            group="B", group_name="拆词组合",
            query=f"{core[0]} {yr} {yr-1} {yr-2} 趋势",
            note=f"锁定近 3 年（{yr-2}–{yr}），含趋势词", checked=False))
    elif time_v == "history":
        items.append(QueryItem(
            group="B", group_name="拆词组合",
            query=f"{core[0]} 历史 起源 沿革",
            note="拉长时间轴，看来龙去脉", checked=False))
    elif time_v == "compare":
        items.append(QueryItem(
            group="B", group_name="拆词组合",
            query=f"{core[0]} 对比 变化 趋势",
            note="以「新旧对比」视角检索", checked=False))

    # C 组：高级指令（2~3 条）
    base = " ".join(core[:2]) if core else q
    items.append(QueryItem(
        group="C", group_name="高级指令", query=f"{base} filetype:pdf",
        note="限定 PDF：白皮书、报告、论文，信息密度高"))
    items.append(QueryItem(
        group="C", group_name="高级指令", query=f'"{core[0]}" {base}' if core else f'"{q}"',
        note="精确短语匹配，锁定关键概念", checked=False))

    # D 组：一手站点定向（按主题路由）
    text_all = q + " " + " ".join(terms)
    matched_routes = 0
    for route in config.SITE_ROUTES:
        if any(topic in text_all for topic in route["topics"]):
            items.append(QueryItem(
                group="D", group_name="站点定向",
                query=f"{base} site:{route['site']}",
                note=f"直达一手来源：{route['name']}"))
            matched_routes += 1
    # 决策依据 / 找支持依据：强制补一条政府站定向，抬高一手权重
    depth_vals = _answer_values(a, "depth")
    stance_vals = _answer_values(a, "stance")
    if matched_routes == 0 or "decision" in depth_vals or "support" in stance_vals:
        items.append(QueryItem(
            group="D", group_name="站点定向",
            query=f"{base} site:gov.cn",
            note="直达一手来源：政府网站（官方口径）", checked=False))

    # E 组：反面搜索（仅在用户明确选「counter」时才生成，默认不出现反面）
    if "counter" in stance_vals:
        counter_base = core[0] if core else q
        available = [w for w in config.COUNTER_WORDS if w not in text_all]
        primary_word = available[0] if available else config.COUNTER_WORDS[0]
        items.append(QueryItem(
            group="E", group_name="反面搜索", query=f"{counter_base} {primary_word}",
            note="你明确选了「听反对的」，补一条反面视角（仅勾选时生成）"))
        extra = available[1:3] if len(available) > 1 else config.COUNTER_WORDS[1:3]
        for w in extra:
            items.append(QueryItem(
                group="E", group_name="反面搜索", query=f"{counter_base} {w}",
                note="再加一条反面视角", checked=False))

    return items


def _answer_values(answers: Dict, key: str) -> List[str]:
    """从 answers 中取某维度的作答。兼容 str / List[str] / List[dict]。"""
    v = (answers or {}).get(key)
    if v is None:
        return []
    if isinstance(v, str):
        return [v]
    if isinstance(v, list):
        out = []
        for item in v:
            if isinstance(item, str):
                out.append(item)
            elif isinstance(item, dict):
                val = item.get("value")
                if isinstance(val, str):
                    out.append(val)
        return out
    return []


def apply_answers_to_terms(base_terms: List[str], answers: Dict[str, str]) -> List[str]:
    """把用户的多角度作答折算进关键词列表（排序 + 追加维度词）。

    支持多选：focus 可以多个 terms 同时选；其他维度仍为单选。
    """
    a = answers or {}
    terms = list(base_terms)

    # 核心指向：把选中词顶到最前（可多选）
    focus_vals = _answer_values(a, "focus")
    if focus_vals and "__all__" not in focus_vals:
        for fv in focus_vals:
            if fv in terms:
                terms.remove(fv)
                terms.insert(0, fv)
        # 附加通用句型词（帮助检索意图）
        intent_words = {
            "__why__": ["原因", "分析"],
            "__how__": ["方法", "步骤", "如何"],
            "__howmany__": ["数据", "统计", "多少"],
            "__which__": ["对比", "区别"],
            "__should__": ["建议", "意见", "值不值得"],
        }
        for fv in focus_vals:
            for w in intent_words.get(fv, []):
                if w not in terms:
                    terms.append(w)

    # 时间窗（取首个生效的）
    time_vals = _answer_values(a, "time")
    for tv in time_vals:
        if tv == "recent":
            yr = datetime.now().year
            terms += [str(yr), str(yr - 1)]
            break
        elif tv == "recent2":
            yr = datetime.now().year
            terms += [str(yr), str(yr - 1), str(yr - 2), "趋势"]
            break
        elif tv == "history":
            terms += ["历史", "起源", "沿革"]
            break
        elif tv == "compare":
            terms += ["对比", "变化", "趋势"]
            break

    # 范围 / 地域
    scope_vals = _answer_values(a, "scope")
    for sv in scope_vals:
        if sv == "domestic":
            terms += ["中国", "国内"]
            break
        elif sv == "global":
            terms += ["海外", "国际"]
            break
        elif sv == "compare":
            terms += ["对比", "中外"]
            break
        # scope == "region" 时用户的 free 文本会直接进入 terms

    # 去重保序
    seen = set()
    out = []
    for x in terms:
        if x not in seen:
            seen.add(x)
            out.append(x)
    return out[:10]


def make_plan(question: str, extra_terms: List[str] = None, answers: Dict[str, str] = None):
    base_terms, jargon = extract_terms(question, extra_terms)
    terms = apply_answers_to_terms(base_terms, answers) if answers else base_terms
    queries = build_query_matrix(question, terms, jargon, answers)
    return terms, jargon, queries
