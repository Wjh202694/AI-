// 多角度追问卡片生成（Python clarifier.py 的 JS 版）
// 每张卡片 ≥5 选项，全部允许自由填空 + 卡内互斥分组

const COMMON_FOCUS_OPTIONS = [
  { value: "__why__", label: "为什么 / 原因", hint: "背后的逻辑和成因", group: "intent" },
  { value: "__how__", label: "怎么办 / 方法", hint: "具体的步骤或对策", group: "intent" },
  { value: "__howmany__", label: "多少 / 数量", hint: "数据、统计、对比数字", group: "intent" },
  { value: "__which__", label: "哪个好 / 对比", hint: "横向比较", group: "intent" },
  { value: "__should__", label: "要不要 / 值不值", hint: "决策建议", group: "intent" },
];

const ALL_OPTIONS = ["strict", "recent", "recent2", "history", "compare"];

/**
 * 根据问题 + 拆词，生成 5 个角度的追问。
 * 每张卡片都 ≥5 选项 + 自由填空 + 互斥分组。
 */
export function buildClarify(question, terms = []) {
  const q = (question || "").trim();
  const timeSensitive = /(现在|目前|今年|最新|趋势|前景|未来|还|值不值|还能|会不会|涨价|降价|政策|补贴|行情|202\d|19\d\d)/.test(q);

  // ① 核心指向：通用句型互斥，terms 之间不互斥
  const focusOpts = [...COMMON_FOCUS_OPTIONS];
  for (const t of terms.slice(0, 6)) {
    if (!focusOpts.some((o) => o.value === t)) {
      focusOpts.push({ value: t, label: t, hint: `围绕「${t}」展开检索`, group: `term:${t}` });
    }
  }
  if (!focusOpts.some((o) => o.value === "__all__")) {
    focusOpts.push({ value: "__all__", label: "都要，全面铺开", hint: "不偏重，广撒网", group: "intent" });
  }

  // ② 时间窗
  const timePrompt = {
    id: "time",
    dimension: "时间窗",
    text: timeSensitive
      ? "这个问题今年的答案和三年前可能完全不同——你想锁定哪个时间范围？"
      : "先划清时间：你要的是当下的现状，还是来龙去脉？",
    options: [
      { value: "recent", label: "只看最近 1 年", hint: "给查询加最新年份", group: "time" },
      { value: "recent2", label: "最近 2–3 年", hint: "兼顾稳定与时效", group: "time" },
      { value: "history", label: "想看历史背景", hint: "加「历史 / 起源 / 沿革」类词", group: "time" },
      { value: "compare", label: "对比新旧差异", hint: "既看过去也看现在", group: "time" },
      { value: "any", label: "不限时间", hint: "广撒网，自己筛", group: "time" },
    ],
    allow_free: true,
    free_hint: "其他时间范围（如「未来 5 年」「某年至今」）",
  };

  // ③ 立场
  const stancePrompt = {
    id: "stance",
    dimension: "立场",
    text: "说句不中听的：多数人只搜支持自己判断的信息。这次你想要哪种？",
    options: [
      { value: "balance", label: "中立全面", hint: "正反都给，自行判断", group: "stance" },
      { value: "counter", label: "我就要听反对的", hint: "加强反面搜索，专治确认偏误", group: "stance" },
      { value: "support", label: "我要找支持依据", hint: "加重一手 / 官方来源权重", group: "stance" },
      { value: "mainstream", label: "主流共识", hint: "找被多数人接受的观点", group: "stance" },
      { value: "academic", label: "学界观点", hint: "优先学术 / 论文 / 研究报告", group: "stance" },
    ],
    allow_free: true,
    free_hint: "其他立场（如「特定利益相关方」）",
  };

  // ④ 用途
  const depthPrompt = {
    id: "depth",
    dimension: "用途",
    text: "你搜这个是要干嘛用？这决定我该把一手资料顶到多高。",
    options: [
      { value: "decision", label: "做决策依据", hint: "重一手、压二手，结论要经得起溯源", group: "depth" },
      { value: "learn", label: "快速了解", hint: "轻重都给，先建立全景", group: "depth" },
      { value: "material", label: "找素材写东西", hint: "广收案例与观点", group: "depth" },
      { value: "quote", label: "找具体数据/引文", hint: "要能直接引用的数字或原话", group: "depth" },
      { value: "argue", label: "说服别人", hint: "要能拿出来打脸的硬料", group: "depth" },
    ],
    allow_free: true,
    free_hint: "其他用途",
  };

  // ⑤ 范围
  const scopePrompt = {
    id: "scope",
    dimension: "范围",
    text: "范围先划清：你关心的是哪片地界上的情况？",
    options: [
      { value: "domestic", label: "国内为主", hint: "加「中国 / 国内」限定", group: "scope" },
      { value: "global", label: "放眼全球", hint: "加「海外 / 国际」限定", group: "scope" },
      { value: "compare", label: "中外对比", hint: "同时看两边的做法", group: "scope" },
      { value: "region", label: "特定地区", hint: "聚焦某个省 / 市 / 国家", group: "scope" },
      { value: "any", label: "不限地域", hint: "中外都收", group: "scope" },
    ],
    allow_free: true,
    free_hint: "具体地区名（如「长三角」「广东省」）",
  };

  // ① 核心指向
  const focusPrompt = {
    id: "focus",
    dimension: "核心指向",
    text: "你这问题里其实藏了好几层意思。先认领一下：你真正想搞清楚的，是下面哪几个？（可多选）",
    options: focusOpts,
    allow_free: true,
    free_hint: "以上都不是，其实我是想问…",
  };

  return [focusPrompt, timePrompt, stancePrompt, depthPrompt, scopePrompt];
}
