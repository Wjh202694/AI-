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

const COUNTER_WORDS = ["质疑", "反对", "风险", "失败", "争议", "后悔", "骗局", "问题"];
const COUNTER_PHRASES = ["局限性", "副作用", "反面观点", "负面影响"];

/**
 * 生成多角度检索矩阵
 * - 1 条原问题
 * - 6 个思考维度（人群/地域/时间/对比/量化/机制）
 * - 1-3 条反例（默认 2 条）
 */
export function buildQueryMatrix(question, terms, jargon, answers = {}) {
  const a = answers || {};
  const items = [];
  const q = (question || "").trim();
  const core = terms.slice(0, 4);
  const base = core.length ? core.join(" ") : q;
  const primary = core[0] || q;

  // 1. 原问题（必出）
  items.push({
    group: "原问题", group_name: "🎯 原问题",
    query: q, checked: true,
    note: "原问题本身，直接搜",
  });

  // 2. 6 个思考角度（衍生子问题）
  for (const ang of ANGLES) {
    items.push({
      group: ang.label, group_name: ang.label,
      query: `${base}${ang.suffix}`,
      checked: ang.defaultChecked,
      note: ang.note,
    });
  }

  // 3. 反例（默认 2 条，support/academic 时去掉）
  const stanceVals = Array.isArray(a.stance) ? a.stance : (a.stance ? [a.stance] : []);
  const skipCounter = stanceVals.includes("support") || stanceVals.includes("academic");
  if (!skipCounter) {
    const counterBase = primary;
    const textAll = (q + " " + terms.join(" ")).toLowerCase().split(/\s+/);
    const available = COUNTER_WORDS.filter((w) => !textAll.includes(w));
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
