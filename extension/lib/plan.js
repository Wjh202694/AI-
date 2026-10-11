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

/**
 * 站点定向路由（按主题匹配）
 */
const SITE_ROUTES = [
  { topics: ["政策", "数据", "统计", "经济", "人口", "就业", "收入", "房价"], site: "stats.gov.cn", name: "国家统计局" },
  { topics: ["公司", "股票", "上市", "财报", "招股", "行业", "企业"], site: "cninfo.com.cn", name: "巨潮资讯网" },
  { topics: ["政策", "法规", "通知", "规定", "国务院"], site: "gov.cn", name: "中国政府网" },
  { topics: ["论文", "研究", "学术", "实验"], site: "arxiv.org", name: "论文预印本库" },
  { topics: ["github", "代码", "开源", "实现"], site: "github.com", name: "GitHub" },
];

const COUNTER_WORDS = ["质疑", "反对", "风险", "失败", "争议", "后悔", "骗局", "问题"];

/**
 * 生成五组查询矩阵 A/B/C/D/E
 */
export function buildQueryMatrix(question, terms, jargon, answers = {}) {
  const a = answers || {};
  const items = [];
  const q = (question || "").trim();

  // A 组：原始问句
  items.push({ group: "A", group_name: "原始问句", query: q, checked: true, note: "直接搜你的原话，作为对照基线" });

  // 核心词
  const core = terms.slice(0, 4);
  if (core.length >= 2) {
    items.push({ group: "B", group_name: "拆词组合", query: core.slice(0, 3).join(" "), checked: true, note: "拆出的核心词 AND 组合，比整句更准" });
    if (core.length >= 3) {
      items.push({ group: "B", group_name: "拆词组合", query: core.slice(0, 2).join(" ") + " 最新", checked: false, note: "加时效词，避开过时信息" });
    }
  }
  if (jargon.length) {
    items.push({ group: "B", group_name: "拆词组合", query: [...core.slice(0, 2), ...jargon.slice(0, 2)].join(" "), checked: true, note: "混入行业黑话：答案所在的地方会这么写" });
  }

  // 时效作答
  const timeVals = Array.isArray(a.time) ? a.time : (a.time ? [a.time] : []);
  const tv = timeVals[0];
  if (tv === "recent") {
    items.push({ group: "B", group_name: "拆词组合", query: `${core[0]} ${yr} ${yr-1} 最新`, checked: false, note: `锁定近 2 年，过滤过时信息` });
  } else if (tv === "recent2") {
    items.push({ group: "B", group_name: "拆词组合", query: `${core[0]} ${yr} ${yr-1} ${yr-2} 趋势`, checked: false, note: `锁定近 3 年，含趋势词` });
  } else if (tv === "history") {
    items.push({ group: "B", group_name: "拆词组合", query: `${core[0]} 历史 起源 沿革`, checked: false, note: "拉长时间轴，看来龙去脉" });
  } else if (tv === "compare") {
    items.push({ group: "B", group_name: "拆词组合", query: `${core[0]} 对比 变化 趋势`, checked: false, note: "以「新旧对比」视角检索" });
  }

  // C 组：高级指令
  const base = core.slice(0, 2).join(" ") || q;
  items.push({ group: "C", group_name: "高级指令", query: `${base} filetype:pdf`, checked: true, note: "限定 PDF：白皮书、报告、论文，信息密度高" });
  if (core[0]) {
    items.push({ group: "C", group_name: "高级指令", query: `"${core[0]}" ${base}`, checked: false, note: "精确短语匹配，锁定关键概念" });
  }

  // D 组：站点定向
  const textAll = (q + " " + terms.join(" ")).toLowerCase();
  let matchedRoutes = 0;
  for (const route of SITE_ROUTES) {
    if (route.topics.some((t) => textAll.includes(t))) {
      items.push({ group: "D", group_name: "站点定向", query: `${base} site:${route.site}`, checked: false, note: `直达一手来源：${route.name}` });
      matchedRoutes++;
    }
  }
  const depthVals = Array.isArray(a.depth) ? a.depth : (a.depth ? [a.depth] : []);
  const stanceVals = Array.isArray(a.stance) ? a.stance : (a.stance ? [a.stance] : []);
  if (matchedRoutes === 0 || depthVals.includes("decision") || stanceVals.includes("support")) {
    items.push({ group: "D", group_name: "站点定向", query: `${base} site:gov.cn`, checked: false, note: "直达一手来源：政府网站（官方口径）" });
  }

  // E 组：反面搜索（仅在用户明确选「counter」时）
  if (stanceVals.includes("counter")) {
    const counterBase = core[0] || q;
    const available = COUNTER_WORDS.filter((w) => !textAll.includes(w));
    const primary = available[0] || COUNTER_WORDS[0];
    items.push({ group: "E", group_name: "反面搜索", query: `${counterBase} ${primary}`, checked: true, note: "你明确选了「听反对的」，补一条反面视角" });
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
