/* 搜绎 · 前端逻辑（全中文） */
"use strict";

const $ = (sel) => document.querySelector(sel);
const state = {
  question: "",
  queries: [],
  baseQueries: [],
  clarify: [],
  answers: {},
  searchId: null,
  lastResults: [],
  aiOn: false,
  llmQuery: null,
  terms: [],
  relevanceTier: "loose",  // 当前档位：strict / balanced / loose
};

/* ---------- 内联 SVG 图标（零二进制资源，单色线性 1.5 描边） ---------- */
const svg = (inner) =>
  `<svg class="ic" viewBox="0 0 24 24" fill="none" stroke="currentColor"
        stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round">${inner}</svg>`;

/* 维度 → 图标 */
const DIM_ICON = {
  focus: svg('<circle cx="12" cy="12" r="3.2"/><path d="M12 3.5v3M12 17.5v3M3.5 12h3M17.5 12h3"/>'),
  time:  svg('<circle cx="12" cy="12" r="8"/><path d="M12 7.5V12l3 2"/>'),
  stance:svg('<path d="M5 19v-7a7 7 0 0 1 14 0v7"/><path d="M3 19h18"/>'),
  depth: svg('<path d="M12 4l7 4v6c0 3.6-3 5.6-7 6-4-.4-7-2.4-7-6V8z"/>'),
  scope: svg('<circle cx="12" cy="12" r="8.2"/><path d="M3.8 12h16.4M12 3.8v16.4"/>'),
};

const ICONS = {
  shield: svg('<path d="M12 3.5l6.5 2.6v4.9c0 3.9-2.7 6.6-6.5 8-3.8-1.4-6.5-4.1-6.5-8V6.1z"/><path d="M9.4 11.9l1.9 1.9 3.5-3.7"/>'),
  help:   svg('<circle cx="12" cy="12" r="8.2"/><path d="M9.4 9.6a2.6 2.6 0 0 1 5 .9c0 1.7-2.4 2.1-2.4 3.6"/><circle cx="12" cy="16.7" r=".9" fill="currentColor" stroke="none"/>'),
  lines:  svg('<line x1="5" y1="8" x2="19" y2="8"/><line x1="5" y1="12" x2="19" y2="12"/><line x1="5" y1="16" x2="14.5" y2="16"/>'),
  warn:   svg('<path d="M12 4l8.4 15H3.6z"/><line x1="12" y1="10" x2="12" y2="14"/><circle cx="12" cy="16.4" r=".9" fill="currentColor" stroke="none"/>'),
  check:  svg('<path d="M5 12.6l4 4L19 6.8"/>'),
};
const BADGE_ICON = { p: ICONS.shield, u: ICONS.help, s: ICONS.lines, c: ICONS.warn };

/* ---------- 工具 ---------- */
function toast(msg, ms = 2200) {
  const t = $("#toast");
  t.textContent = msg;
  t.classList.remove("hidden");
  clearTimeout(t._timer);
  t._timer = setTimeout(() => t.classList.add("hidden"), ms);
}

function escapeHtml(s) {
  return (s || "").replace(/[&<>"']/g, (c) => ({
    "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;",
  }[c]));
}

async function api(path, options) {
  const resp = await fetch(path, options);
  if (!resp.ok) {
    let detail = `请求失败（${resp.status}）`;
    try {
      const j = await resp.json();
      const d = j && j.detail;
      if (typeof d === "string") {
        detail = d;
      } else if (Array.isArray(d)) {
        // Pydantic 422 校验错误：detail 是数组，转成可读文本
        detail = d.map((e) => {
          const loc = Array.isArray(e.loc) ? e.loc.join(".") : "";
          return `${loc}: ${e.msg}`;
        }).join("；");
      } else if (d) {
        detail = String(d);
      }
    } catch (_) { /* 响应不是 JSON，保持默认 detail */ }
    throw new Error(detail);
  }
  return resp.json();
}

function debounce(fn, ms) {
  let t;
  return (...a) => { clearTimeout(t); t = setTimeout(() => fn(...a), ms); };
}

function cleanAnswers(src) {
  const clean = {};
  for (const [k, v] of Object.entries(src)) {
    if (v == null) continue;
    if (typeof v === "string") {
      if (v.startsWith("__free__")) clean[k] = v.slice(8);
      else clean[k] = v;
    } else if (Array.isArray(v)) {
      const out = [];
      for (const item of v) {
        if (typeof item === "string") {
          if (item) out.push(item.startsWith("__free__") ? item.slice(8) : item);
        } else if (item && typeof item === "object" && item.value) {
          let val = item.value;
          if (typeof val === "string" && val.startsWith("__free__")) val = val.slice(8);
          if (val) out.push(val);
        }
      }
      if (out.length) clean[k] = out;
    }
  }
  return clean;
}

/* ---------- 绎字解线动效 ---------- */
function playYixian() {
  const el = $("#yixian");
  if (!el) return;
  if (window.matchMedia && window.matchMedia("(prefers-reduced-motion: reduce)").matches) return;
  el.classList.remove("unravel");
  void el.offsetWidth;          // 强制回流，确保每次都能重播
  el.classList.add("unravel");
}

/* ---------- 第一步：生成检索方案（默认直接出矩阵，盘问可折叠） ---------- */
async function makePlan() {
  const question = $("#question").value.trim();
  if (!question) { toast("请先输入你的问题"); return; }
  state.question = question;
  state.answers = {};
  state.llmQuery = null;
  $("#plan-btn").disabled = true;
  $("#matrix-panel").classList.add("hidden");
  $("#results").classList.add("hidden");
  $("#overview-bar").classList.add("hidden");
  $("#results-preview").classList.add("hidden");    // 开始新一轮时藏掉
  playYixian();
  try {
    const data = await api("/api/plan", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ question, extra_terms: [] }),
    });
    state.clarify = data.clarify || [];
    state.baseQueries = data.queries;
    state.queries = data.queries;
    state.terms = data.terms || [];
    renderClarify();                          // 强制盘问：先展示追问面板
    $("#clarify-panel").classList.remove("hidden");
    // 自动滚动到追问面板，避免用户没注意到
    requestAnimationFrame(() => $("#clarify-panel").scrollIntoView({ behavior: "smooth", block: "start" }));
    // 矩阵暂不展示，须先完成盘问（proceedFromClarify）才出现
  } catch (e) {
    toast("生成检索方案失败：" + e.message);
  } finally {
    $("#plan-btn").disabled = false;
  }
}

/* 把 LLM 推荐检索式作为独立分组并入 state.queries（保证勾选状态可同步） */
function applyLlm() {
  state.queries = state.queries.filter((q) => q.group !== "L");
  if (state.llmQuery) {
    state.queries.push({
      group: "L", group_name: "AI 推荐检索式",
      query: state.llmQuery, checked: true,
      note: "由云端大模型改写，已默认勾选，可取消",
    });
  }
}

/* 渲染多角度追问卡片：多选 + 同 group 互斥 */
function _answerList(dim) {
  const v = state.answers[dim];
  if (!v) return [];
  if (typeof v === "string") return [v];
  if (Array.isArray(v)) return v;
  return [];
}

function _hasAnswer(dim, val) {
  return _answerList(dim).includes(val);
}

function _toggleAnswer(dim, val, group) {
  const list = _answerList(dim);
  // 1) 先检查是否已选（点击同一个选项 → 取消选中）
  const existIdx = list.findIndex(
    (item) => typeof item === "object" && item && item.value === val
  );
  if (existIdx >= 0) {
    list.splice(existIdx, 1);
    if (!list.length) delete state.answers[dim];
    return;
  }
  // 2) 未选：移除同 group 下的其他旧选项（互斥），再加入新选项
  const filtered = list.filter((item) => {
    if (typeof item !== "object" || !item) return true;
    return item.group !== group;
  });
  filtered.push({ value: val, group });
  state.answers[dim] = filtered;
}

function renderClarify() {
  const wrap = $("#clarify-list");
  wrap.innerHTML = "";
  state.clarify.forEach((p, idx) => {
    const card = document.createElement("div");
    card.className = "clarify-card";
    card.style.animation = `matrixIn .32s ease both ${(idx * 0.07).toFixed(2)}s`;
    const ic = DIM_ICON[p.id] || ICONS.help;
    let optsHtml = "";
    p.options.forEach((o) => {
      const sel = _hasAnswer(p.id, o.value) ? " selected" : "";
      const grp = o.group || "";
      optsHtml += `<button type="button" class="opt multi${sel}" data-dim="${escapeHtml(p.id)}" data-val="${escapeHtml(o.value)}" data-group="${escapeHtml(grp)}">
          <span class="opt-check" aria-hidden="true"></span>
          <span class="opt-body">
            <span class="opt-label">${escapeHtml(o.label)}</span>
            ${o.hint ? `<span class="opt-hint">${escapeHtml(o.hint)}</span>` : ""}
          </span>
        </button>`;
    });
    const freeHtml = p.allow_free
      ? `<div class="opt-free">
           <input type="text" class="free-input" data-dim="${escapeHtml(p.id)}"
                  placeholder="${escapeHtml(p.free_hint || "其他补充…")}">
         </div>`
      : "";
    card.innerHTML = `
      <div class="clarify-head">
        <span class="dim-ic">${ic}</span>
        <span class="dim-tag">${escapeHtml(p.dimension)}</span>
        <span class="dim-hint-multi">可多选</span>
      </div>
      <p class="clarify-text">${escapeHtml(p.text)}</p>
      <div class="opt-row">${optsHtml}</div>
      ${freeHtml}`;
    wrap.appendChild(card);
  });

  wrap.querySelectorAll(".opt.multi").forEach((btn) => {
    btn.addEventListener("click", () => {
      const dim = btn.dataset.dim;
      const val = btn.dataset.val;
      const group = btn.dataset.group || "";
      _toggleAnswer(dim, val, group);
      // 重渲染本卡片：只重画 selected 状态
      wrap.querySelectorAll(`.opt[data-dim="${dim}"]`).forEach((b) => {
        b.classList.remove("selected");
      });
      _answerList(dim).forEach((item) => {
        if (typeof item === "object" && item && item.value) {
          const b = wrap.querySelector(`.opt[data-dim="${dim}"][data-val="${cssEscape(item.value)}"]`);
          if (b) b.classList.add("selected");
        }
      });
      const fi = wrap.querySelector(`.free-input[data-dim="${dim}"]`);
      if (fi) fi.value = "";
      livePreviewDebounced();
    });
  });
  wrap.querySelectorAll(".free-input").forEach((inp) => {
    inp.addEventListener("input", () => {
      const dim = inp.dataset.dim;
      const txt = inp.value.trim();
      if (txt) {
        // 自由输入：替换为单元素数组，group = ""（不互斥）
        state.answers[dim] = [{ value: "__free__" + txt, group: "__free__" }];
        wrap.querySelectorAll(`.opt[data-dim="${dim}"]`).forEach((b) => b.classList.remove("selected"));
      } else {
        delete state.answers[dim];
      }
      livePreviewDebounced();
    });
  });
}

/* CSS.escape 兼容垫片 */
function cssEscape(s) {
  if (window.CSS && CSS.escape) return CSS.escape(s);
  return String(s).replace(/[^a-zA-Z0-9_-]/g, (c) => "\\" + c);
}

/* 选项点选即时预览拆词（防乷）：只同步 state.terms / state.queries，不渲染矩阵。
   矩阵的正式呈现需要用户点击「据此生成检索方案」后才会出现。*/
async function livePreview() {
  const clean = cleanAnswers(state.answers);
  try {
    const data = await api("/api/plan", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ question: state.question, extra_terms: [], answers: clean }),
    });
    // 只静默更新 state，不渲染矩阵。
    state.terms = data.terms || state.terms;
    state.queries = data.queries || state.queries;
  } catch (e) { /* 静默：作答预览失败不影响后续 */ }
}
const livePreviewDebounced = debounce(livePreview, 450);

/* 收起盘问面板 */
function finishClarify() {
  $("#clarify-panel").classList.add("hidden");
  $("#matrix-live-tag").classList.add("hidden");
  $("#matrix-panel").classList.remove("live");
}

/* 强制盘问后据此生成意图确认面板：必经步骤，没有跳过入口 */
async function proceedFromClarify() {
  await livePreview();                         // 同步 state.queries/terms
  finishClarify();
  $("#clarify-panel").classList.add("hidden"); // 彻底藏
  $("#matrix-panel").classList.add("hidden");  // 矩阵暂藏，等确认后再亮
  renderInterpretPanel();                      // 出“我理解”面板
  $("#interpret-panel").scrollIntoView({ behavior: "smooth", block: "start" });
}

/* 打包意图描述：原问句 + 拆词 + 追问选项转中文文本 */
function buildIntentText(question, terms, answers) {
  const q = (question || "").trim();
  const ts = (terms || []).filter(Boolean);
  const cleaned = cleanAnswers(answers);
  // 推论中文补充词（支持多选：某值被选中即追加对应补充）
  const extras = [];
  const _has = (dim, val) => {
    const x = cleaned[dim];
    if (Array.isArray(x)) return x.includes(val);
    return x === val;
  };
  if (_has("time", "recent")) extras.push("最近三年内的官方公告与年报数据");
  if (_has("time", "history")) extras.push("历史变化与沿革");
  if (_has("stance", "积极")) extras.push("正面肯定性资料");
  if (_has("stance", "消极")) extras.push("负面反映与提示问题");
  if (_has("stance", "counter")) extras.push("质疑/反对观点");
  if (_has("depth", "decision")) extras.push("可作为决策依据的权威来源");
  if (_has("depth", "data")) extras.push("关键数额/原始数据");
  if (_has("scope", "domestic")) extras.push("仅限中国境内");
  if (_has("scope", "global")) extras.push("包括海外口径");
  // focus 多选：列出每个选中词
  const focusList = cleaned.focus;
  if (focusList) {
    const arr = Array.isArray(focusList) ? focusList : [focusList];
    const focusLabels = {
      "__why__": "原因", "__how__": "方法", "__howmany__": "数量/数据",
      "__which__": "对比", "__should__": "建议",
    };
    for (const f of arr) {
      if (f && f !== "__all__") {
        extras.push(`重点是「${focusLabels[f] || f}」`);
      }
    }
  }
  // 其他答案原样追加
  const ans = [];
  for (const [k, v] of Object.entries(cleaned)) {
    if (["time", "stance", "depth", "scope", "focus"].includes(k)) continue;
    if (v) ans.push(Array.isArray(v) ? v.join(" ") : v);
  }
  const parts = [q, ...ts, ...ans, ...extras].filter(Boolean);
  return parts.join(" ");
}

/* 渲染“我理解”面板：可读上下文 + 可编辑意图文本 + 返回/确认 */
function renderInterpretPanel() {
  $("#interpret-panel").classList.remove("hidden");
  const intent = buildIntentText(state.question, state.terms, state.answers);
  $("#ip-orig").textContent = state.question || "（空）";
  const ul = $("#ip-answers");
  ul.innerHTML = "";
  const cleaned = cleanAnswers(state.answers);
  const labels = { focus: "重点", time: "时间", stance: "立场", depth: "深度", scope: "范围" };
  let any = false;
  for (const [dim, val] of Object.entries(cleaned)) {
    if (!val) continue;
    any = true;
    const text = Array.isArray(val) ? val.join("、") : val;
    const li = document.createElement("li");
    li.innerHTML = `<b>${escapeHtml(labels[dim] || dim)}</b>${escapeHtml(text)}`;
    ul.appendChild(li);
  }
  $("#ip-answers-block").style.display = any ? "" : "none";

  const ta = $("#ip-text");
  ta.value = intent;
  // 实时同步拆词预览
  const renderTerms = () => {
    const t = $("#ip-terms");
    t.innerHTML = "";
    state.terms.forEach((w) => {
      const c = document.createElement("span");
      c.className = "term-chip";
      c.textContent = w;
      t.appendChild(c);
    });
  };
  renderTerms();
  // 用户编辑文本 → 本地高亮底，进到 confirmInterpretation 才真正发后端
}

/* 用户点了确认：以面板中的文本作为新“问句”重建拆词与矩阵 */
async function confirmInterpretation() {
  const txt = $("#ip-text").value.trim();
  if (!txt) { toast("请输入你想检索的问题描述"); return; }
  $("#ip-confirm").disabled = true;
  $("#ip-confirm").textContent = "正在生成…";
  try {
    // 以编辑后的文本重建拆词 + 矩阵（带上原追问选项以保持质量）
    const data = await api("/api/plan", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        question: txt,
        extra_terms: [],
        answers: cleanAnswers(state.answers),
      }),
    });
    state.question = txt;                       // 后续检索以这个文本为准
    state.terms = data.terms || [];
    state.baseQueries = data.queries;
    state.queries = data.queries;
    applyLlm();
    renderMatrix({ terms: state.terms, queries: state.queries });
    $("#interpret-panel").classList.add("hidden");
    $("#matrix-panel").scrollIntoView({ behavior: "smooth", block: "start" });
    if (state.aiOn) await fetchLlm();
  } catch (e) {
    toast("生成检索方案失败：" + e.message);
  } finally {
    $("#ip-confirm").disabled = false;
    $("#ip-confirm").textContent = "确认生成检索方案";
  }
}

/* 返回追问面板 */
function backToClarify() {
  $("#interpret-panel").classList.add("hidden");
  $("#clarify-panel").classList.remove("hidden");
  $("#clarify-panel").scrollIntoView({ behavior: "smooth", block: "start" });
}

function renderMatrix(data, scroll = true, animate = true) {
  $("#matrix-panel").classList.remove("hidden");
  $("#terms-view").textContent =
    data.terms.length ? "拆词：" + data.terms.join("、") : "";
  const wrap = $("#matrix-groups");
  wrap.innerHTML = "";

  const groups = {};
  for (const q of data.queries) {
    (groups[q.group] = groups[q.group] || { name: q.group_name, items: [] }).items.push(q);
  }

  // 反面组（E）固定排到最后
  const entries = Object.entries(groups).sort(([a]) => (a === "E" ? 1 : 0));
  let gi = 0;
  for (const [g, info] of entries) {
    const div = document.createElement("div");
    div.className = "qgroup" + (g === "E" ? " counter" : "") + (g === "L" ? " llm" : "");
    const headWarn = g === "E" ? `<span class="qhead-ic">${ICONS.warn}</span>` : "";
    const headNote = g === "L" ? `（由大模型改写，可取消勾选）`
      : (g === "E" ? "（每个观点，强制搜一次反面）" : "");
    div.innerHTML = `<div class="qgroup-head">${headWarn}${escapeHtml(info.name)}${
      headNote ? `<span class="qhead-note">${headNote}</span>` : ""}</div>`;
    const base = gi * 0.09;
    const delay = (g === "E" ? base + 0.15 : base).toFixed(2) + "s";
    div.style.animation = animate ? `matrixIn .34s ease both ${delay}` : "none";
    gi++;
    info.items.forEach((q, i) => {
      const row = document.createElement("div");
      row.className = "qitem";
      row.innerHTML = `
        <input type="checkbox" ${q.checked ? "checked" : ""} data-g="${g}" data-i="${i}">
        <input type="text" class="qtext" value="${escapeHtml(q.query)}" data-g="${g}" data-i="${i}">
        <span class="qnote">${escapeHtml(q.note || "")}</span>`;
      div.appendChild(row);
    });
    wrap.appendChild(div);
  }
  if (scroll) $("#matrix-panel").scrollIntoView({ behavior: "smooth", block: "start" });
}

function collectQueries() {
  document.querySelectorAll("#matrix-groups input[type=checkbox]").forEach((cb) => {
    const q = findQuery(cb.dataset.g, cb.dataset.i);
    if (q) q.checked = cb.checked;
  });
  document.querySelectorAll("#matrix-groups input.qtext").forEach((inp) => {
    const q = findQuery(inp.dataset.g, inp.dataset.i);
    if (q) q.query = inp.value.trim();
  });
  return state.queries.filter((q) => q.checked && q.query);
}

function findQuery(g, i) {
  const list = state.queries.filter((x) => x.group === g);
  return list[Number(i)];
}

/* ---------- AI 增强：取推荐检索式 ---------- */
async function fetchLlm() {
  try {
    const data = await api("/api/llm", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ question: state.question, terms: state.terms || [] }),
    });
    if (data.available && data.query) {
      state.llmQuery = data.query;
      applyLlm();
      renderMatrix({ terms: state.terms, queries: state.queries }, false, false);
    } else if (data.available === false) {
      toast("AI增强未配置：后端设置 SOUYI_LLM_* 环境变量即可开启，已用规则生成");
    }
  } catch (e) { /* 静默降级为纯规则 */ }
}

/* ---------- 第二步：执行搜索 ---------- */
async function runSearch(tierOverride) {
  const checked = collectQueries();
  if (!checked.length) { toast("请至少勾选一条查询"); return; }

  // 强防御：tier 必须是三个合法值之一，否则兑底为 "loose"
  const ALLOWED_TIERS = ["strict", "balanced", "loose"];
  let tier = tierOverride || state.relevanceTier;
  if (typeof tier !== "string" || !ALLOWED_TIERS.includes(tier)) {
    tier = "loose";
  }
  state.relevanceTier = tier;  // 同步 state，避免下次仍是废值

  // 入参健全性检查：避免因 state 错乱导致后端 422
  if (!state.question || typeof state.question !== "string" || !state.question.trim()) {
    toast("问题文本丢失，请重新生成检索方案");
    return;
  }
  if (!Array.isArray(state.queries) || !state.queries.length) {
    toast("检索方案为空，请重新生成");
    return;
  }

  $("#loading").classList.remove("hidden");
  $("#results").classList.add("hidden");
  $("#overview-bar").classList.add("hidden");
  $("#search-btn").disabled = true;

  let data;
  try {
    const payload = {
      question: state.question,
      queries: state.queries,
      llm_used: state.aiOn && !!state.llmQuery,
      terms: Array.isArray(state.terms) ? state.terms : [],
      relevance_tier: tier,
    };
    data = await api("/api/search", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
  } catch (e) {
    console.error("[runSearch] 错误:", e);
    let detail = e && e.message ? e.message : String(e || "未知错误");
    if (!detail || detail === "[object Object]" || detail === "object") {
      detail = "未知错误，请查看浏览器控制台（F12）获取详情";
    } else if (detail.includes("Failed to fetch") || detail.includes("NetworkError")) {
      detail = "网络问题：搜绎服务可能未运行";
    }
    toast("搜索失败：" + detail, 4000);
    return;
  } finally {
    $("#loading").classList.add("hidden");
    $("#search-btn").disabled = false;
  }

  // 渲染放到 try 外：渲染异常不影响搜索已完成的状态
  try {
    if (!data) return;
    state.searchId = data.search_id || null;
    state.lastResults = Array.isArray(data.results) ? data.results : [];
    state.relevanceTier = data.relevance_tier || tier;
    renderOverview(data.status || [], data.stats || {},
                   data.relax_threshold || 0,
                   data.filtered_total || 0,
                   data.relevance_tier || tier);
    renderResults(state.lastResults);
    $("#results").classList.remove("hidden");
    $("#results").scrollIntoView({ behavior: "smooth", block: "start" });
  } catch (e) {
    console.error("[runSearch] 渲染错误:", e);
    toast("结果渲染失败：" + e.message, 4000);
  }
}

/* 阈值放宽弹窗（已废弃：默认档位已是宽松 30%） */
function askRelaxDialog() {
  /* 默认档位为 loose（30%），基本总能拿到结果，不再需要弹窗。
     保留空函数以避免遗留调用崩溃。 */
}

function renderOverview(statusList, stats, relaxThreshold, filteredTotal, tier) {
  const bar = $("#overview-bar");
  bar.classList.remove("hidden");
  bar.classList.remove("anim-chan");
  void bar.offsetWidth;
  bar.classList.add("anim-chan");
  bar.innerHTML = "";

  const left = document.createElement("div");
  left.className = "ov-left";
  const CHAN_NAME = { web: "公开网络", site: "一手站点" };
  for (const s of statusList) {
    const item = document.createElement("span");
    item.className = "ov-chan";
    const cls = s.ok ? "ok" : "bad";
    item.innerHTML = `<i class="dot ${cls}"></i><span class="ov-name">${CHAN_NAME[s.channel] || s.channel}</span>` +
      (s.count ? `<span class="ov-num">${s.count}</span>` : "");
    item.title = s.message;
    left.appendChild(item);
  }
  // 档位提示
  if (tier) {
    const tag = document.createElement("span");
    tag.className = "ov-thresh ov-thresh-" + tier;
    const tierLabel = {
      "strict":   "严格 80%",
      "balanced": "平衡 60%",
      "loose":    "宽松 30%",
    }[tier] || tier;
    const pct = (typeof relaxThreshold === "number") ? `${(relaxThreshold * 100).toFixed(0)}%` : "";
    const flt = (typeof filteredTotal === "number") ? `${filteredTotal} 候选` : "";
    tag.textContent = `档位：${tierLabel}${pct ? " · " + pct : ""}${flt ? " · " + flt : ""}`;
    tag.title = "可点击右上「调整档位」按钮切换";
    left.appendChild(tag);
  }

  const right = document.createElement("div");
  right.className = "ov-right";
  const chips = [
    ["p", "一手", stats.primary], ["u", "存疑", stats.unsure],
    ["s", "二手", stats.secondary], ["c", "反面", stats.counter],
  ];
  for (const [k, label, n] of chips) {
    const span = document.createElement("span");
    span.className = "stat " + k;
    span.textContent = `${label} ${n}`;
    right.appendChild(span);
  }

  bar.appendChild(left);
  bar.appendChild(right);
}

/* ---------- 结果渲染 ---------- */
const SECTIONS = [
  { key: "p", title: "一手资料 · 可下结论", filter: (r) => r.grade === "primary" && !r.is_counter },
  { key: "u", title: "存疑待核 · 需交叉验证", filter: (r) => r.grade === "unsure" && !r.is_counter },
  { key: "s", title: "二手线索 · 仅作参考", filter: (r) => r.grade === "secondary" && !r.is_counter },
  { key: "c", title: "反面搜索 · 看完两边再判断", filter: (r) => r.is_counter },
];

function renderResults(results) {
  const wrap = $("#result-sections");
  wrap.innerHTML = "";
  let any = false;

  const GROUP_STEP = 0.12;
  const CARD_STEP = 0.04;
  let groupIndex = 0;
  for (const sec of SECTIONS) {
    const list = results.filter(sec.filter);
    const div = document.createElement("div");
    div.className = "rsection " + sec.key;
    const groupDelay = groupIndex * GROUP_STEP;
    const no = String(groupIndex + 1).padStart(2, "0");
    div.innerHTML = `<div class="rsection-title">
        <span class="rsection-no">${no}</span>
        <span class="rsection-name">${sec.title}</span>
        <span class="rsection-count">${list.length} 条</span>
      </div>`;
    div.style.animation = `resultIn .32s ease both ${groupDelay.toFixed(2)}s`;
    if (list.length) {
      any = true;
      list.forEach((r, i) => {
        const d = groupDelay + Math.min(i * CARD_STEP, 0.5);
        const card = renderCard(r, sec.key, d);
        card.style.animation = `resultIn .32s ease both ${d.toFixed(2)}s`;
        div.appendChild(card);
      });
    } else {
      // 空节依然渲染，不隐匿；给出明确「无」与一句原因
      const empty = document.createElement("div");
      empty.className = "rsection-empty";
      const isCounter = sec.key === "c";
      empty.innerHTML = `
        <div class="rsempty-mark">无</div>
        <div class="rsempty-text">
          ${isCounter
            ? `本次未检索到针对该问题的反面观点，请手工查阅或换关键字后再试`
            : `本次未检索到该级别的结果`}
        </div>`;
      div.appendChild(empty);
    }
    wrap.appendChild(div);
    groupIndex++;
  }

  if (!any) {
    // 4 节全是““无”：多加一个全局提示，但保留 4 节结构
    const banner = document.createElement("div");
    banner.className = "hempty";
    banner.textContent = "本次检索全线未返结果，请调整检索方案后重试。";
    wrap.prepend(banner);
  }
}

function renderCard(r, secKey, delay = 0) {
  const card = document.createElement("div");
  card.className = "rcard " + (r.is_counter ? "c" : secKey);
  const badgeClass = r.is_counter ? "c"
    : r.grade === "primary" ? "p" : r.grade === "unsure" ? "u" : "s";
  const badgeIc = BADGE_ICON[badgeClass] || "";
  const gradeText = r.is_counter ? "反面视角" : (r.grade_label || "");
  const link = r.url || "";
  const shownUrl = link || "";
  const deepTag = r.is_official_deep ? `<span class="deep-tag">官方直达</span>` : "";
  const staleTag = r.stale ? `<span class="stale-tag">年代较久</span>` : "";
  const relevanceTag = (r.relevance === "relaxed")
    ? `<span class="relevance-tag-relaxed" title="${escapeHtml(r.relevance_reasons || '放宽阈值后保留，请人工核验')}">⚠️ 边缘相关</span>`
    : "";
  const proof = r.provenance_note
    ? `<div class="rcard-proof"><span class="proof-label">溯源 · </span>${escapeHtml(r.provenance_note)}</div>`
    : "";
  const relevanceProof = (r.relevance === "relaxed" && r.relevance_reasons)
    ? `<div class="rcard-proof"><span class="proof-label">相关度 · </span>${escapeHtml(r.relevance_reasons)}</div>`
    : "";
  card.innerHTML = `
    <div class="rcard-top">
      <span class="badge ${badgeClass} badge-pop" style="animation-delay:${delay.toFixed(2)}s">${badgeIc}${escapeHtml(gradeText)}</span>
      ${deepTag}${staleTag}${relevanceTag}
      <span class="domain">${escapeHtml(r.domain || "")}</span>
    </div>
    <h3>${link
      ? `<a href="${escapeHtml(link)}" target="_blank" rel="noopener" data-clickable="1">${escapeHtml(r.title)}</a>`
      : escapeHtml(r.title)}</h3>
    <div class="rsnippet">${escapeHtml(r.snippet || "")}</div>
    ${proof}${relevanceProof}
    <div class="rcard-foot">
      ${shownUrl ? `<span class="rurl" title="点击复制链接">${escapeHtml(shownUrl)}</span>` : ""}
      <span class="rmeta">命中查询：${escapeHtml(r.source_query || "")}</span>
      ${shownUrl ? `<span class="copy-link">复制链接</span>` : ""}
    </div>`;
  const doCopy = () => {
    navigator.clipboard.writeText(shownUrl).then(
      () => toast("链接已复制"),
      () => toast("复制失败，请手动选择复制"));
  };
  const urlEl = card.querySelector(".rurl");
  const copyEl = card.querySelector(".copy-link");
  if (urlEl) urlEl.addEventListener("click", doCopy);
  if (copyEl) copyEl.addEventListener("click", doCopy);
  // 点击埋点：用户点标题打开新窗口 → 上报一次
  const titleLink = card.querySelector("a[data-clickable='1']");
  if (titleLink) {
    titleLink.addEventListener("click", () => recordClick(link));
  }
  return card;
}

/* 点击埋点上报（POST /api/click） */
function recordClick(url) {
  if (!url) return;
  try {
    const body = JSON.stringify({ url });
    // 优先 sendBeacon（页面跳转/关闭也能发出），失败 fallback fetch
    if (navigator.sendBeacon) {
      const blob = new Blob([body], { type: "application/json" });
      const ok = navigator.sendBeacon("/api/click", blob);
      if (ok) return;
    }
    fetch("/api/click", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body,
      keepalive: true,
    }).catch(() => { /* 静默忽略 */ });
  } catch (e) { /* 静默忽略 */ }
}

/* ---------- 导出 / 复制 ---------- */
async function exportMarkdown() {
  if (!state.searchId) { toast("还没有可导出的搜索结果"); return; }
  try {
    const resp = await fetch(`/api/export/${state.searchId}`);
    if (!resp.ok) throw new Error("导出失败");
    const md = await resp.text();
    const blob = new Blob([md], { type: "text/markdown;charset=utf-8" });
    const a = document.createElement("a");
    a.href = URL.createObjectURL(blob);
    a.download = `搜索记录_${state.question.slice(0, 20)}.md`;
    a.click();
    URL.revokeObjectURL(a.href);
    toast("已导出笔记文件");
  } catch (e) {
    toast(e.message);
  }
}

async function copyAll() {
  if (!state.searchId) { toast("还没有可复制的结果"); return; }
  try {
    const resp = await fetch(`/api/export/${state.searchId}`);
    const md = await resp.text();
    await navigator.clipboard.writeText(md);
    toast("全部结果已复制到剪贴板");
  } catch (e) {
    toast("复制失败：" + e.message);
  }
}

/* ---------- 历史抽屉 ---------- */
async function openHistory() {
  const drawer = $("#history-drawer");
  const mask = $("#drawer-mask");
  drawer.classList.remove("hidden");
  mask.classList.remove("hidden");
  void drawer.offsetWidth;
  drawer.classList.add("open");
  mask.classList.add("open");
  const list = $("#history-list");
  list.innerHTML = `<div class="hempty">正在读取…</div>`;
  try {
    const data = await api("/api/history");
    if (!data.items.length) {
      list.innerHTML = `<div class="hempty">暂无搜索记录</div>`;
      return;
    }
    list.innerHTML = "";
    for (const item of data.items) {
      const div = document.createElement("div");
      div.className = "hitem";
      div.innerHTML = `
        <div class="hq">${escapeHtml(item.question)}</div>
        <div class="hm"><span>${item.created_at}</span><span>${item.result_count} 条结果</span></div>`;
      div.addEventListener("click", () => loadHistoryDetail(item.id));
      list.appendChild(div);
    }
  } catch (e) {
    list.innerHTML = `<div class="hempty">读取失败：${escapeHtml(e.message)}</div>`;
  }
}

async function loadHistoryDetail(id) {
  try {
    const data = await api(`/api/history/${id}`);
    closeHistory();
    state.question = data.question;
    state.searchId = data.id;
    $("#question").value = data.question;
    state.queries = data.query_matrix;
    renderMatrix({ terms: [], queries: data.query_matrix });
    const results = data.results.map((r) => ({
      channel: r.channel, grade: r.grade,
      grade_label: r.grade_label || (r.grade === "primary" ? "一手·可下结论"
        : r.grade === "secondary" ? "二手·仅找线索" : "存疑·需交叉验证"),
      title: r.title, url: r.url, snippet: r.snippet,
      domain: r.domain || "", source_query: r.source_query || "",
      is_counter: !!r.is_counter, provenance_note: r.provenance_note || "",
      stale: !!r.stale, is_official_deep: !!r.is_official_deep,
      relevance: r.relevance || "high",
      relevance_reasons: r.relevance_reasons || "",
      stale: !!r.stale, is_official_deep: !!r.is_official_deep,
    }));
    state.lastResults = results;
    renderResults(results);
    $("#results").classList.remove("hidden");
    toast("已回看历史记录");
  } catch (e) {
    toast("读取历史失败：" + e.message);
  }
}

function closeHistory() {
  const drawer = $("#history-drawer");
  const mask = $("#drawer-mask");
  drawer.classList.remove("open");
  mask.classList.remove("open");
  drawer.classList.add("hidden");
  mask.classList.add("hidden");
}

/* ---------- 事件绑定 ---------- */
$("#plan-btn").addEventListener("click", makePlan);
$("#question").addEventListener("keydown", (e) => { if (e.key === "Enter") makePlan(); });
$("#refine-btn").addEventListener("click", proceedFromClarify);
if ($("#ip-confirm")) $("#ip-confirm").addEventListener("click", confirmInterpretation);
if ($("#ip-back"))     $("#ip-back").addEventListener("click", backToClarify);
document.querySelectorAll(".ex-chip").forEach((chip) => {
  chip.addEventListener("click", () => {
    $("#question").value = chip.dataset.q;
    makePlan();
  });
});
$("#search-btn").addEventListener("click", runSearch);

/* 档位切换：点击档位按钮 → 更新 state → 可重跑 search */
function _selectTier(tier) {
  state.relevanceTier = tier;
  document.querySelectorAll("#tier-bar .tier-opt").forEach((btn) => {
    const active = btn.dataset.tier === tier;
    btn.classList.toggle("active", active);
    btn.setAttribute("aria-checked", active ? "true" : "false");
  });
}
document.querySelectorAll("#tier-bar .tier-opt").forEach((btn) => {
  btn.addEventListener("click", () => _selectTier(btn.dataset.tier));
});
// 初始化默认档位
_selectTier(state.relevanceTier);
$("#export-btn").addEventListener("click", exportMarkdown);
$("#copy-btn").addEventListener("click", copyAll);
$("#history-btn").addEventListener("click", openHistory);
$("#history-close").addEventListener("click", closeHistory);
$("#drawer-mask").addEventListener("click", closeHistory);
$("#hint-close").addEventListener("click", () => $("#hint-bar").classList.add("hidden"));

/* ---------- 一键演示：一路跑到结果，绕过追问 ---------- */
const DEMO_QUESTION = "某上市公司近三年研发投入是多少";

async function demoFlow() {
  const btn = $("#ex-demo");
  if (btn) { btn.disabled = true; btn.textContent = "演示中…"; }
  $("#question").value = DEMO_QUESTION;
  // 1) 生成方案
  await makePlan();
  // 2) 给每个追问维度自动填上第一个选项（统一用 list 格式，避免与 _toggleAnswer 不兼容）
  for (const p of state.clarify) {
    if (!state.answers[p.id] && p.options && p.options.length) {
      const o = p.options[0];
      state.answers[p.id] = [{ value: o.value, group: o.group || "" }];
    }
  }
  // 3) 生成意图面板
  await proceedFromClarify();
  // 4) demo 跳过用户评审，直接以默认文本确认
  await confirmInterpretation();
  // 6) 默认勾上 A、B、C 三组（在 DOM 上直接改，runSearch 会从这里读）
  const KEEP = ["A", "B", "C", "E"];
  document.querySelectorAll("#matrix-groups input[type=checkbox]").forEach((cb) => {
    cb.checked = KEEP.includes(cb.dataset.g);
  });
  // 5) 执行搜索
  await runSearch();
  if (btn) { btn.disabled = false; btn.textContent = "看示例结果（跳过追问）"; }
}
if ($("#ex-demo")) $("#ex-demo").addEventListener("click", demoFlow);

/* ---------- 示例 / 最近结果预览 ---------- */
// 三个预置示例（无历史时用，都是真域名、可点）
const SAMPLE_RESULTS = [
  {
    grade: "primary", grade_label: "一手·可下结论",
    title: "上海证券交易所 | IPO 信息专区",
    url:   "https://www.sse.com.cn/ipo/home/",
    domain:"sse.com.cn",
    snippet:"新动态IPO审核、发行上市公告、上市公司临时停牌、披露等一手信息"
  },
  {
    grade: "primary", grade_label: "一手·可下结论",
    title: "中国证监会指定信息披露平台 · 巨潮资讯网",
    url:   "http://www.cninfo.com.cn/",
    domain:"cninfo.com.cn",
    snippet:"上市公司公告、年报、招股说明书、公司财务、股东变动等即时公告"
  },
  {
    grade: "primary", grade_label: "一手·可下结论",
    title: "国家统计局 · 统计数据查询",
    url:   "https://www.stats.gov.cn/",
    domain:"stats.gov.cn",
    snippet:"人口、就业、CPI、工资、产业结构等官方数据发布入口，可下结论"
  },
];

async function renderPreview() {
  const wrap = $("#preview-cards");
  const tag  = $("#preview-tag");
  const qEl  = $("#preview-q");
  const allBtn = $("#preview-all");
  const cntEl  = $("#preview-count");
  if (!wrap) return;
  wrap.innerHTML = "";

  let items = [];
  try { items = (await api("/api/history")).items || []; } catch (_) {}

  let mode = "history", q = "", total = 0, picks = [];
  if (items.length) {
    const top = items[0];                                       // 最近一次
    q = top.question; total = top.result_count;
    try {
      const detail = await api(`/api/history/${top.id}`);
      picks = (detail.results || []).slice(0, 4);
    } catch (_) {}
  }
  if (!picks.length) {
    mode = "sample"; q = ""; total = 3; picks = SAMPLE_RESULTS;
    tag.textContent = "示例";
  } else {
    tag.textContent = "最近一次";
    // 绑定查看全部 -> 点这个历史项
    allBtn.href = "#";
    allBtn.onclick = (e) => { e.preventDefault(); loadHistoryDetail(items[0].id); };
  }
  qEl.textContent = q;
  cntEl.textContent = total;
  allBtn.hidden = mode !== "history";

  picks.forEach((r, i) => {
    const card = document.createElement("div");
    const k = r.is_counter ? "c" : (r.grade === "primary" ? "p" : r.grade === "unsure" ? "u" : "s");
    card.className = "preview-card " + k;
    card.style.animation = `resultIn .28s ease both ${(i * 0.06).toFixed(2)}s`;
    const badge = `<span class="badge ${k}">${escapeHtml(r.grade_label || r.grade || "")}</span>`;
    const domain = `<span class="domain">${escapeHtml(r.domain || "")}</span>`;
    const link = r.url || "";
    const host = (() => { try { return new URL(link).host.replace(/^www\./, ""); } catch (_) { return r.domain || ""; } })();
    card.innerHTML = `
      <div class="pc-meta">${badge}${domain}</div>
      <h3><a href="${escapeHtml(link)}" target="_blank" rel="noopener">${escapeHtml(r.title || "")}</a></h3>
      <div class="pc-snippet">${escapeHtml(r.snippet || "")}</div>
      <a class="pc-jump" href="${escapeHtml(link)}" target="_blank" rel="noopener" title="访问 ${escapeHtml(host)}">访问</a>`;
    wrap.appendChild(card);
  });
}

if ($("#results-preview")) renderPreview();

/* URL ?demo=1 一打开就跳原仓库链接供 demo;?demoPause=interpret 停在确认面板 */
if (new URLSearchParams(location.search).get("demo") === "1") {
  setTimeout(async () => {
    if (new URLSearchParams(location.search).get("demoPause") === "interpret") {
      // 只跑到「我的理解」面板，不自动确认
      $("#question").value = DEMO_QUESTION;
      await makePlan();
      for (const p of state.clarify) {
        if (!state.answers[p.id] && p.options && p.options.length) {
          state.answers[p.id] = p.options[0].value;
        }
      }
      await proceedFromClarify();
    } else {
      demoFlow();
    }
  }, 300);
}

/* AI 增强开关 */
$("#ai-toggle").addEventListener("change", (e) => {
  const on = e.target.checked;
  state.aiOn = on;
  $("#ai-state").textContent = on ? "已开启" : "已关闭";
  if (!on) {
    state.llmQuery = null;
    applyLlm();
    renderMatrix({ terms: state.terms || [], queries: state.queries }, false, false);
    return;
  }
  if (state.queries.length) fetchLlm();
});
