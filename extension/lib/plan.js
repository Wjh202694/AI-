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

// 6 个思考角度的衍生模板
// 每条都从同一原始问题出发，生成一个不同维度的「子问题」
const ANGLES = [
  {
    key: "audience",
    label: "👥 人群维度",
    suffix: " 不同人群 青少年 成人 老人",
    note: "按人群拆解：青少年 / 成人 / 老人 / 职业群体",
    defaultChecked: false,
  },
  {
    key: "region",
    label: "🌍 地域维度",
    suffix: " 中国 美国 欧洲 日本 对比",
    note: "按地域拆解：中国 / 海外 / 特定地区 的差异",
    defaultChecked: false,
    detectConflict: "country",
  },
  {
    key: "time",
    label: "⏱ 时间维度",
    suffix: " 短期 长期 趋势 历史",
    note: "按时间拆解：短期 vs 长期 / 历史趋势 / 最新",
    defaultChecked: false,
  },
  {
    key: "compare",
    label: "⚖ 对比维度",
    suffix: " vs 对比 区别 差异",
    note: "对比相似事物：A vs B / 区别 / 差异",
    defaultChecked: false,
  },
  {
    key: "quantify",
    label: "📊 量化维度",
    suffix: " 数据 统计 数字 百分比 报告",
    note: "要具体数字：数据 / 统计 / 百分比 / 报告",
    defaultChecked: true,
  },
  {
    key: "mechanism",
    label: "🔬 机制维度",
    suffix: " 原因 原理 机制 为什么",
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

const COUNTER_WORDS = ["质疑", "反对", "风险", "失败", "争议", "后悔", "骗局", "问题"];
const COUNTER_PHRASES = ["局限性", "副作用", "反面观点", "负面影响"];

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
  const base = core.length ? core.join(" ") : q;
  const primary = core[0] || q;
  const textAll = (q + " " + terms.join(" ")).toLowerCase();

  // 1. 原问题（必出）
  items.push({
    group: "原问题", group_name: "🎯 原问题",
    query: q, checked: true,
    note: "原问题本身，直接搜",
  });

  // 2. 6 个思考角度（衍生子问题）
  const COUNTRY_WORDS = ["中国", "美国", "日本", "韩国", "欧洲", "德国", "法国", "英国", "俄罗斯", "印度", "日本", "加拿大", "澳洲", "澳大利亚"];
  const containsCountry = COUNTRY_WORDS.some((c) => textAll.includes(c));
  for (const ang of ANGLES) {
    let suffix = ang.suffix;
    let note = ang.note;
    // 冲突检测：原问题已含国家词时，地域维度不要再硬塞“中国”
    if (ang.detectConflict === "country" && containsCountry) {
      const otherCountries = COUNTRY_WORDS.filter((c) => !textAll.includes(c)).slice(0, 4);
      suffix = " 对比 " + otherCountries.join(" ");
      note = `按地域拆解：与其他地区（${otherCountries.slice(0, 2).join("、")} 等）对比`;
    }
    items.push({
      group: ang.label, group_name: ang.label,
      query: `${base}${suffix}`,
      checked: ang.defaultChecked,
      note: note,
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

  // 5. 反面视角（默认 2 条，counter 时加 1 条，support/academic 时去掉）
  const stanceVals = Array.isArray(a.stance) ? a.stance : (a.stance ? [a.stance] : []);
  const skipCounter = stanceVals.includes("support") || stanceVals.includes("academic");
  if (!skipCounter) {
    const counterBase = primary;
    const textAllWords = textAll.split(/\s+/);
    const available = COUNTER_WORDS.filter((w) => !textAllWords.includes(w));
    const w1 = available[0] || COUNTER_WORDS[0];
    const w2 = available[1] || COUNTER_WORDS[1] || COUNTER_PHRASES[0];
    items.push({
      group: "反面视角", group_name: "⚠ 反面视角",
      query: `${counterBase} ${w1}`,
      checked: false,
      note: "⚠ 反面视角（仅供参考）— 看完两边才有资格判断",
    });
    items.push({
      group: "反面视角", group_name: "⚠ 反面视角",
      query: `${counterBase} ${w2} 局限`,
      checked: false,
      note: "⚠ 反面视角（仅供参考）— 质疑/局限性视角",
    });
    if (stanceVals.includes("counter")) {
      const w3 = available[2] || COUNTER_WORDS[2] || COUNTER_PHRASES[1];
      items.push({
        group: "反面视角", group_name: "⚠ 反面视角",
        query: `${counterBase} ${w3}`,
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
