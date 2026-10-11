# -*- coding: utf-8 -*-
"""多角度追问（grill-me 风格）：在出方案前逼出用户问题里的模糊点。

v3 (2026-10)：多选支持 + 互斥分组。
- time/stance/depth/scope：卡内全互斥（group=prompt.id）
- focus：通用句型互斥（group="intent"）；每个 term 独立 group（可多选不同 terms）
"""

import re
from datetime import datetime
from typing import List

from .models import ClarifyPrompt, ClarifyOption


def build_clarify(question: str, terms: List[str], jargon: List[str]) -> List[ClarifyPrompt]:
    """根据问题 + 拆词，生成 5 个角度的追问。每张卡片都 ≥5 选项 + 自由填空 + 互斥分组。"""
    q = question.strip()
    prompts: List[ClarifyPrompt] = []

    # —— 通用兜底词库 ——
    focus_common = [
        ClarifyOption(value="__why__", label="为什么 / 原因",
                      hint="我其实想知道背后的逻辑和成因", group="intent"),
        ClarifyOption(value="__how__", label="怎么办 / 方法",
                      hint="我要找具体的步骤或对策", group="intent"),
        ClarifyOption(value="__howmany__", label="多少 / 数量",
                      hint="我要的是数据、统计、对比数字", group="intent"),
        ClarifyOption(value="__which__", label="哪个好 / 对比",
                      hint="我在多个选项之间犹豫，需要横向比较", group="intent"),
        ClarifyOption(value="__should__", label="要不要 / 值不值",
                      hint="我做不做这件事本身需要建议", group="intent"),
    ]

    # ① 核心指向：通用句型互斥，terms 之间不互斥（每个 term 独立 group）
    focus_opts = list(focus_common)
    for t in terms[:6]:
        if not any(o.value == t for o in focus_opts):
            # 每个 term 独立 group：同 term 之间互斥（同一 term 不会重复出现）
            focus_opts.append(ClarifyOption(value=t, label=t,
                                            hint=f"围绕「{t}」展开检索",
                                            group=f"term:{t}"))
    if not any(o.value == "__all__" for o in focus_opts):
        focus_opts.append(ClarifyOption(value="__all__", label="都要，全面铺开",
                                        hint="不偏重，广撒网", group="intent"))
    prompts.append(ClarifyPrompt(
        id="focus",
        dimension="核心指向",
        text="你这问题里其实藏了好几层意思。先认领一下：你真正想搞清楚的，是下面哪几个？（可多选）",
        options=focus_opts,
        allow_free=True,
        free_hint="以上都不是，其实我是想问…",
    ))

    # ② 时间窗：卡内全互斥（group="time"）
    time_sensitive = bool(re.search(
        r"(现在|目前|今年|最新|趋势|前景|未来|还|值不值|还能|会不会|涨价|降价|政策|补贴|行情|202\d|19\d\d)",
        q))
    prompts.append(ClarifyPrompt(
        id="time",
        dimension="时间窗",
        text=("这个问题今年的答案和三年前可能完全不同——你想锁定哪个时间范围？"
              if time_sensitive else
              "先划清时间：你要的是当下的现状，还是来龙去脉？"),
        options=[
            ClarifyOption(value="recent", label="只看最近 1 年", hint="给查询加最新年份", group="time"),
            ClarifyOption(value="recent2", label="最近 2–3 年", hint="兼顾稳定与时效", group="time"),
            ClarifyOption(value="history", label="想看历史背景", hint="加「历史 / 起源 / 沿革」类词", group="time"),
            ClarifyOption(value="compare", label="对比新旧差异", hint="既看过去也看现在", group="time"),
            ClarifyOption(value="any", label="不限时间", hint="广撒网，自己筛", group="time"),
        ],
        allow_free=True,
        free_hint="其他时间范围（如「未来 5 年」「某年至今」）",
    ))

    # ③ 立场：卡内全互斥
    prompts.append(ClarifyPrompt(
        id="stance",
        dimension="立场",
        text="说句不中听的：多数人只搜支持自己判断的信息。这次你想要哪种？",
        options=[
            ClarifyOption(value="balance", label="中立全面", hint="正反都给，自行判断", group="stance"),
            ClarifyOption(value="counter", label="我就要听反对的", hint="加强反面搜索，专治确认偏误", group="stance"),
            ClarifyOption(value="support", label="我要找支持依据", hint="加重一手 / 官方来源权重", group="stance"),
            ClarifyOption(value="mainstream", label="主流共识", hint="找被多数人接受的观点", group="stance"),
            ClarifyOption(value="academic", label="学界观点", hint="优先学术 / 论文 / 研究报告", group="stance"),
        ],
        allow_free=True,
        free_hint="其他立场（如「特定利益相关方」）",
    ))

    # ④ 用途 / 深度：卡内全互斥
    prompts.append(ClarifyPrompt(
        id="depth",
        dimension="用途",
        text="你搜这个是要干嘛用？这决定我该把一手资料顶到多高。",
        options=[
            ClarifyOption(value="decision", label="做决策依据", hint="重一手、压二手，结论要经得起溯源", group="depth"),
            ClarifyOption(value="learn", label="快速了解", hint="轻重都给，先建立全景", group="depth"),
            ClarifyOption(value="material", label="找素材写东西", hint="广收案例与观点", group="depth"),
            ClarifyOption(value="quote", label="找具体数据/引文", hint="要能直接引用的数字或原话", group="depth"),
            ClarifyOption(value="argue", label="说服别人", hint="要能拿出来打脸的硬料", group="depth"),
        ],
        allow_free=True,
        free_hint="其他用途",
    ))

    # ⑤ 范围 / 地域：卡内全互斥
    prompts.append(ClarifyPrompt(
        id="scope",
        dimension="范围",
        text="范围先划清：你关心的是哪片地界上的情况？",
        options=[
            ClarifyOption(value="domestic", label="国内为主", hint="加「中国 / 国内」限定", group="scope"),
            ClarifyOption(value="global", label="放眼全球", hint="加「海外 / 国际」限定", group="scope"),
            ClarifyOption(value="compare", label="中外对比", hint="同时看两边的做法", group="scope"),
            ClarifyOption(value="region", label="特定地区", hint="聚焦某个省 / 市 / 国家", group="scope"),
            ClarifyOption(value="any", label="不限地域", hint="中外都收", group="scope"),
        ],
        allow_free=True,
        free_hint="具体地区名（如「长三角」「广东省」）",
    ))

    return prompts


def year_hint() -> str:
    """当前年份，用于时效类提示文案。"""
    return str(datetime.now().year)
