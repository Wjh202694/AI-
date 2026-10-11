// 拆词 + 查询矩阵生成（Python query_planner.py 的 JS 版）
import { JARGON_MAP, STOP_WORDS, SPLIT_RE } from "./jargon.js";

/**
 * 从问句中拆出关键词，并命中行业黑话映射。
 * @returns {[terms, jargon]}
 */
export function extractTerms(question, extraTerms = []) {
  const text = (question || "").trim();
  if (!text) return [[], []];
  const rawTokens = text.split(SPLIT_RE).filter(Boolean);

  const terms = [];
  const jargon = [];
  const hitKeys = [];

  // 整句匹配黑话映射
  for (const [key, expansions] of Object.entries(JARGON_MAP)) {
    if (text.includes(key)) {
      jargon.push(...expansions);
      hitKeys.push(key);
      if (!terms.includes(key) && !STOP_WORDS.has(key)) {
        terms.push(key);
      }
    }
  }

  // 按 token 拆词
  const stopSorted = [...STOP_WORDS].sort((a, b) => b.length - a.length);
  const stopLong = stopSorted.filter((w) => w.length >= 2);
  const stopOne = stopSorted.filter((w) => w.length === 1);

  for (const token of rawTokens) {
    let cleaned = token;
    for (const key of hitKeys) cleaned = cleaned.split(key).join(" ");
    for (const sw of stopLong) cleaned = cleaned.split(sw).join(" ");
    cleaned = cleaned.trim();
    while (cleaned && stopOne.some((w) => cleaned.startsWith(w)) && cleaned.length > 2) {
      cleaned = cleaned.slice(1);
    }
    while (cleaned && stopOne.some((w) => cleaned.endsWith(w)) && cleaned.length > 2) {
      cleaned = cleaned.slice(0, -1);
    }
    for (const piece of cleaned.split(/\s+/).map((s) => s.trim()).filter(Boolean)) {
      if (piece && !STOP_WORDS.has(piece) && !terms.includes(piece)) {
        if (piece.length < 2 && !/[A-Za-z0-9]/.test(piece)) continue;
        terms.push(piece);
      }
    }
  }

  // 合并 extraTerms
  for (const t of extraTerms || []) {
    const tt = (t || "").trim();
    if (tt && !terms.includes(tt)) jargon.push(tt);
  }

  // 去重保序
  const seen = new Set();
  const jargonUniq = jargon.filter((x) => !seen.has(x) && seen.add(x));

  return [terms.slice(0, 8), jargonUniq.slice(0, 8)];
}

/**
 * 把用户的多角度作答折算进关键词列表。
 */
export function applyAnswersToTerms(baseTerms, answers) {
  const a = answers || {};
  const terms = [...baseTerms];
  const yr = new Date().getFullYear();

  const _vals = (k) => {
    const v = a[k];
    if (!v) return [];
    return Array.isArray(v) ? v : [v];
  };

  // 核心指向：把选中词顶到最前（多选）
  const focusVals = _vals("focus").filter((x) => x !== "__all__");
  for (const fv of focusVals) {
    if (terms.includes(fv)) {
      terms.splice(terms.indexOf(fv), 1);
      terms.unshift(fv);
    }
    const intentWords = {
      __why__: ["原因", "分析"],
      __how__: ["方法", "步骤", "如何"],
      __howmany__: ["数据", "统计", "多少"],
      __which__: ["对比", "区别"],
      __should__: ["建议", "意见", "值不值得"],
    };
    for (const w of intentWords[fv] || []) {
      if (!terms.includes(w)) terms.push(w);
    }
  }

  // 时间窗
  for (const tv of _vals("time")) {
    if (tv === "recent") { terms.push(String(yr), String(yr - 1)); break; }
    if (tv === "recent2") { terms.push(String(yr), String(yr - 1), String(yr - 2), "趋势"); break; }
    if (tv === "history") { terms.push("历史", "起源", "沿革"); break; }
    if (tv === "compare") { terms.push("对比", "变化", "趋势"); break; }
  }

  // 范围
  for (const sv of _vals("scope")) {
    if (sv === "domestic") { terms.push("中国", "国内"); break; }
    if (sv === "global") { terms.push("海外", "国际"); break; }
    if (sv === "compare") { terms.push("对比", "中外"); break; }
  }

  // 去重保序
  const seen = new Set();
  return terms.filter((x) => !seen.has(x) && seen.add(x)).slice(0, 10);
}

// 6 个思考角度的衍生模板（每条都是完整自然问句，不是关键词堆叠）
// base 参数是用户的原问题，模板把它自然地嵌入问句中
const ANGLES = [
  {
    key: "audience",
    label: "👥 人群维度",
    template: (base) => `不同人群（青少年、成年人、老年人、不同职业）的「${base}」有什么差异？`,
    note: "按人群拆解：青少年 / 成人 / 老人 / 职业群体",
    defaultChecked: false,
  },
  {
    key: "region",
    label: "🌍 地域维度",
    template: (base, others) => `不同地区（中国、美国、欧洲、日本 等）的「${base}」对比与差异是什么？`,
    note: "按地域拆解：中国 / 海外 / 特定地区 的差异",
    defaultChecked: false,
    detectConflict: "country",
  },
  {
    key: "time",
    label: "⏱ 时间维度",
    template: (base) => `短期与长期的「${base}」有什么不同？近年来的变化趋势是什么？`,
    note: "按时间拆解：短期 vs 长期 / 历史趋势 / 最新",
    defaultChecked: false,
  },
  {
    key: "compare",
    label: "⚖ 对比维度",
    template: (base) => `「${base}」与同类相近的事物对比，区别和优劣是什么？`,
    note: "对比相似事物：A vs B / 区别 / 差异",
    defaultChecked: false,
  },
  {
    key: "quantify",
    label: "📊 量化维度",
    template: (base) => `「${base}」的具体数据 / 统计 / 数字 / 百分比是多少？有哪些权威报告？`,
    note: "要具体数字：数据 / 统计 / 百分比 / 报告",
    defaultChecked: true,
  },
  {
    key: "mechanism",
    label: "🔬 机制维度",
    template: (base) => `为什么「${base}」？背后的原因 / 原理 / 机制是什么？`,
    note: "追问原理：原因 / 原理 / 机制 / 为什么",
    defaultChecked: true,
  },
];

// 站点定向路由（按主题智能匹配）
const SITE_ROUTES = [
  { topics: ["政策", "数据", "统计", "经济", "人口", "就业", "收入", "房价"], site: "stats.gov.cn", name: "国家统计局" },
  { topics: ["公司", "股票", "上市", "财报", "招股", "行业", "企业"], site: "cninfo.com.cn", name: "巨潮资讯网" },
  { topics: ["政策", "法规", "通知", "规定", "国务院"], site: "gov.cn", name: "中国政府网" },
  { topics: ["论文", "研究", "学术", "实验"], site: "arxiv.org", name: "论文预印本库" },
  { topics: ["github", "代码", "开源", "实现"], site: "github.com", name: "GitHub" },
];

const COUNTER_TEMPLATES = [
  (core) => `质疑：${core}这种说法是否被夸大或误导？有什么反例？`,
  (core) => `${core}的局限性、副作用或负面影响有哪些？`,
  (core) => `为什么${core}的观点可能是错的？有哪些质疑和反驳？`,
];

/**
 * 生成多角度检索矩阵
 * - 1 条原问题
 * - 6 个思考维度（人群/地域/时间/对比/量化/机制）
 * - 高级指令：PDF 限定 + 精确短语（保留）
 * - 站点定向：按主题智能匹配（保留）
 * - 1-3 条反例
 */
export function buildQueryMatrix(question, terms, jargon, answers = {}) {
  const a = answers || {};
  const items = [];
  const q = (question || "").trim();
  const core = terms.slice(0, 4);
  // base 用原问题作为模板填字（不是空格拼接的核心词）让语句更自然
  const base = q;
  const primary = core[0] || q;
  const textAll = (q + " " + terms.join(" ")).toLowerCase();

  // 1. 原问题（必出）
  items.push({
    group: "原问题", group_name: "🎯 原问题",
    query: q, checked: true,
    note: "原问题本身，直接搜",
  });

  // 2. 6 个思考角度（完整问句模板）
  const COUNTRY_WORDS = ["中国", "美国", "日本", "韩国", "欧洲", "德国", "法国", "英国", "俄罗斯", "印度", "加拿大", "澳洲", "澳大利亚"];
  const containsCountry = COUNTRY_WORDS.some((c) => textAll.includes(c));
  for (const ang of ANGLES) {
    let query, note;
    if (ang.detectConflict === "country" && containsCountry) {
      const otherCountries = COUNTRY_WORDS.filter((c) => !textAll.includes(c)).slice(0, 4);
      query = ang.template(base, otherCountries);
      note = `与其他地区（${otherCountries.slice(0, 3).join("、")} 等）对比`;
    } else {
      query = ang.template(base);
      note = ang.note;
    }
    items.push({
      group: ang.label, group_name: ang.label,
      query,
      checked: ang.defaultChecked,
      note,
    });
  }

  // 3. 高级指令：PDF 文档 + 精确短语
  items.push({
    group: "高级指令", group_name: "📄 PDF 文档",
    query: `${base} filetype:pdf`,
    checked: true,
    note: "限定 PDF：白皮书 / 报告 / 论文 / 研究，信息密度高",
  });
  if (core[0]) {
    items.push({
      group: "高级指令", group_name: "🔤 精确短语",
      query: `"${core[0]}" ${base}`,
      checked: false,
      note: "精确短语匹配，锁定关键概念不被稀释",
    });
  }

  // 4. 站点定向（按主题智能匹配）
  let matchedRoutes = 0;
  for (const route of SITE_ROUTES) {
    if (route.topics.some((t) => textAll.includes(t))) {
      items.push({
        group: "站点定向", group_name: `🌐 ${route.name}`,
        query: `${base} site:${route.site}`,
        checked: false,
        note: `直达一手来源：${route.name}（${route.site}）`,
      });
      matchedRoutes++;
    }
  }
  // 没匹配到任何 routes → fallback 加 gov.cn
  if (matchedRoutes === 0) {
    items.push({
      group: "站点定向", group_name: "🌐 政府网站",
      query: `${base} site:gov.cn`,
      checked: false,
      note: "直达一手来源：政府网站（官方口径）",
    });
  }

  // 5. 反面视角（默认 2 条完整问句，counter 时加 1 条，support/academic 时去掉）
  const stanceVals = Array.isArray(a.stance) ? a.stance : (a.stance ? [a.stance] : []);
  const skipCounter = stanceVals.includes("support") || stanceVals.includes("academic");
  if (!skipCounter) {
    items.push({
      group: "反面视角", group_name: "⚠ 反面视角",
      query: COUNTER_TEMPLATES[0](base),
      checked: false,
      note: "⚠ 反面视角（仅供参考）— 质疑/反例视角",
    });
    items.push({
      group: "反面视角", group_name: "⚠ 反面视角",
      query: COUNTER_TEMPLATES[1](base),
      checked: false,
      note: "⚠ 反面视角（仅供参考）— 局限/副作用视角",
    });
    if (stanceVals.includes("counter")) {
      items.push({
        group: "反面视角", group_name: "⚠ 反面视角",
        query: COUNTER_TEMPLATES[2](base),
        checked: true,
        note: "⚠ 反面视角（你明确选了「听反对的」，加一条深度反面）",
      });
    }
  }

  return items;
}

/**
 * 主入口：生成 plan（terms + 矩阵）
 */
export function makePlan(question, extraTerms = [], answers = {}) {
  const [baseTerms, jargon] = extractTerms(question, extraTerms);
  const terms = applyAnswersToTerms(baseTerms, answers);
  const queries = buildQueryMatrix(question, terms, jargon, answers);
  return { terms, jargon, queries };
}
