// 搜绎 - 侧边栏主逻辑
import { extractTerms, buildQueryMatrix, applyAnswersToTerms } from "./lib/plan.js";
import { buildClarify } from "./lib/clarifier.js";

const state = {
  question: "",
  answers: {},
  queries: [],
  terms: [],
};

// ===== 工具函数 =====
const $ = (s) => document.querySelector(s);

function toast(msg, ms = 1800) {
  const el = $("#toast");
  el.textContent = msg;
  el.classList.remove("hidden");
  clearTimeout(el._timer);
  el._timer = setTimeout(() => el.classList.add("hidden"), ms);
}

const ESC_AMP = '&';
const ESC_LT = '<';
const ESC_GT = '>';
const ESC_QUOT = '"';
const ESC_APOS = '&#39;';
function escapeHtml(s) {
  return String(s || "").replace(/[&<>"']/g, (c) => {
    if (c === "&") return ESC_AMP;
    if (c === "<") return ESC_LT;
    if (c === ">") return ESC_GT;
    if (c === '"') return ESC_QUOT;
    if (c === "'") return ESC_APOS;
    return c;
  });
}

function debounce(fn, ms) {
  let t;
  return (...a) => { clearTimeout(t); t = setTimeout(() => fn(...a), ms); };
}

// ===== 多选答案状态 =====
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
  const existIdx = list.findIndex(
    (item) => typeof item === "object" && item && item.value === val
  );
  if (existIdx >= 0) {
    list.splice(existIdx, 1);
    if (!list.length) delete state.answers[dim];
    return;
  }
  const filtered = list.filter((item) => {
    if (typeof item !== "object" || !item) return true;
    return item.group !== group;
  });
  filtered.push({ value: val, group });
  state.answers[dim] = filtered;
}

// ===== 渲染 =====
function renderClarify(clarify) {
  const wrap = $("#clarify-list");
  wrap.innerHTML = "";
  clarify.forEach((p) => {
    const card = document.createElement("div");
    card.className = "clarify-card";
    let optsHtml = "";
    p.options.forEach((o) => {
      const sel = _hasAnswer(p.id, o.value) ? " selected" : "";
      const grp = o.group || "";
      optsHtml += `<button type="button" class="opt${sel}" data-dim="${escapeHtml(p.id)}" data-val="${escapeHtml(o.value)}" data-group="${escapeHtml(grp)}" title="${escapeHtml(o.hint || '')}">
        ${escapeHtml(o.label)}${o.hint ? ` <span class="opt-hint">${escapeHtml(o.hint)}</span>` : ""}
      </button>`;
    });
    const freeHtml = p.allow_free
      ? `<div class="opt-free"><input type="text" class="free-input" data-dim="${escapeHtml(p.id)}" placeholder="${escapeHtml(p.free_hint || '其他补充…')}"></div>`
      : "";
    card.innerHTML = `
      <div class="clarify-head">
        <span class="dim-tag">${escapeHtml(p.dimension)}</span>
        <span class="dim-hint-multi">可多选</span>
      </div>
      <p class="clarify-text">${escapeHtml(p.text)}</p>
      <div class="opt-row">${optsHtml}</div>
      ${freeHtml}`;
    wrap.appendChild(card);
  });

  wrap.querySelectorAll(".opt").forEach((btn) => {
    btn.addEventListener("click", () => {
      const dim = btn.dataset.dim;
      const val = btn.dataset.val;
      const group = btn.dataset.group || "";
      _toggleAnswer(dim, val, group);
      wrap.querySelectorAll(`.opt[data-dim="${dim}"]`).forEach((b) => b.classList.remove("selected"));
      _answerList(dim).forEach((item) => {
        if (typeof item === "object" && item && item.value) {
          const b = wrap.querySelector(`.opt[data-dim="${dim}"][data-val="${cssEscape(item.value)}"]`);
          if (b) b.classList.add("selected");
        }
      });
    });
  });
  wrap.querySelectorAll(".free-input").forEach((inp) => {
    inp.addEventListener("input", () => {
      const dim = inp.dataset.dim;
      const txt = inp.value.trim();
      if (txt) {
        state.answers[dim] = [{ value: "__free__" + txt, group: "__free__" }];
        wrap.querySelectorAll(`.opt[data-dim="${dim}"]`).forEach((b) => b.classList.remove("selected"));
      } else {
        delete state.answers[dim];
      }
    });
  });
}

function cssEscape(s) {
  if (window.CSS && CSS.escape) return CSS.escape(s);
  return String(s).replace(/[^a-zA-Z0-9_-]/g, (c) => "\\" + c);
}

function renderMatrix(terms, queries) {
  const tv = $("#terms-view");
  tv.textContent = terms.length ? "拆词：" + terms.join("、") : "";

  const wrap = $("#matrix-groups");
  wrap.innerHTML = "";

  // 为每个检索式生成一张独立卡片（用户可逐条复制）
  queries.forEach((q, idx) => {
    const isCounter = (q.group === "E") || (q.group_name && q.group_name.includes("反面"));
    const card = document.createElement("div");
    card.className = "query-card" + (isCounter ? " counter" : "");
    const isWarn = q.note && q.note.startsWith("⚠");
    const noteHtml = isWarn
      ? `<span class="warn">${escapeHtml(q.note)}</span>`
      : escapeHtml(q.note || "");
    card.dataset.idx = String(idx);
    card.innerHTML = `
      <div class="qc-head">
        <span class="qc-angle">${escapeHtml(q.group_name || q.group)}</span>
        <button type="button" class="qc-copy" title="复制这条检索式">📋 复制</button>
      </div>
      <div class="qc-body">
        <input type="text" class="qc-text" value="${escapeHtml(q.query)}">
      </div>
      <div class="qc-note">${noteHtml}</div>`;
    wrap.appendChild(card);
  });

  // 为每张卡片绑定复制按钮
  wrap.querySelectorAll(".query-card").forEach((card) => {
    const copyBtn = card.querySelector(".qc-copy");
    const textInput = card.querySelector(".qc-text");
    if (copyBtn && textInput) {
      copyBtn.addEventListener("click", () => copyOne(textInput.value.trim()));
    }
    // 用户编辑文本后，回写 state.queries（便于复制全部时同步）
    if (textInput) {
      textInput.addEventListener("input", () => {
        const idx = Number(card.dataset.idx);
        if (state.queries[idx]) state.queries[idx].query = textInput.value;
      });
    }
  });
}

// 复制单条检索式到剪贴板
async function copyOne(text) {
  if (!text) { toast("检索式为空"); return; }
  try {
    await navigator.clipboard.writeText(text);
    toast(`已复制：「${text.slice(0, 28)}${text.length > 28 ? "…" : ""}」`);
  } catch (e) {
    toast("复制失败，请手动选择");
  }
}

// ===== 主流程 =====
async function generatePlan() {
  const q = $("#question").value.trim();
  if (!q) { toast("请先输入问题"); return; }
  state.question = q;
  state.answers = {};

  const [baseTerms] = extractTerms(q);
  const clarify = buildClarify(q, baseTerms);
  state.terms = baseTerms;
  state.queries = buildQueryMatrix(q, baseTerms, [], {});

  $("#clarify-panel").classList.remove("hidden");
  $("#plan-panel").classList.add("hidden");
  renderClarify(clarify);
  $("#clarify-panel").scrollIntoView({ behavior: "smooth", block: "nearest" });
}

function refinePlan() {
  const terms = applyAnswersToTerms(state.terms, state.answers);
  state.queries = buildQueryMatrix(state.question, terms, [], state.answers);
  state.terms = terms;
  renderMatrix(terms, state.queries);

  $("#plan-panel").classList.remove("hidden");
  $("#plan-panel").scrollIntoView({ behavior: "smooth", block: "nearest" });
}

function collectAll() {
  // 不需 checkbox：收集当前 DOM 中的所有检索式（按用户编辑过的最新值）
  const out = [];
  document.querySelectorAll("#matrix-groups .qc-text").forEach((inp) => {
    const v = (inp.value || "").trim();
    if (v) out.push(v);
  });
  return out;
}

async function copyAll() {
  const queries = collectAll();
  if (!queries.length) { toast("没有检索式可复制"); return; }
  try {
    await navigator.clipboard.writeText(queries.join("\n"));
    toast(`已复制全部 ${queries.length} 条`);
  } catch (e) {
    toast("复制失败，请手动选择");
  }
}

async function copyJSON() {
  const payload = {
    question: state.question,
    terms: state.terms,
    answers: state.answers,
    queries: state.queries,
  };
  try {
    await navigator.clipboard.writeText(JSON.stringify(payload, null, 2));
    toast("已复制 JSON");
  } catch (e) {
    toast("复制失败");
  }
}

function reset() {
  state.question = "";
  state.answers = {};
  state.terms = [];
  state.queries = [];
  $("#question").value = "";
  $("#clarify-panel").classList.add("hidden");
  $("#plan-panel").classList.add("hidden");
  $("#grab-btn").classList.add("hidden");
  $("#input-panel").scrollIntoView({ behavior: "smooth", block: "nearest" });
}

// ===== 监听 background.js 传来的选中文本 =====
chrome.storage.onChanged.addListener((changes) => {
  const key = "souyi.lastSelected";
  if (changes[key]) {
    const v = changes[key].newValue;
    if (v && v.text) {
      $("#question").value = v.text;
      $("#grab-btn").classList.remove("hidden");
      $("#grab-btn").textContent = `用选中文本（${v.text.length} 字）`;
      toast("已捕获选中文本", 1500);
    }
  }
});

chrome.storage.local.get("souyi.lastSelected", (data) => {
  if (data && data.souyi.lastSelected && data.souyi.lastSelected.text) {
    const v = data.souyi.lastSelected;
    $("#question").value = v.text;
    $("#grab-btn").classList.remove("hidden");
    $("#grab-btn").textContent = `用选中文本（${v.text.length} 字）`;
  }
});

// 按钮事件
document.addEventListener("DOMContentLoaded", () => {
  $("#generate-btn").addEventListener("click", generatePlan);
  $("#refine-btn").addEventListener("click", refinePlan);
  $("#copy-all-btn").addEventListener("click", copyAll);
  $("#copy-json-btn").addEventListener("click", copyJSON);
  $("#reset-btn").addEventListener("click", reset);
  $("#grab-btn").addEventListener("click", () => {
    const t = $("#question").value.trim();
    if (t) toast("已填入选中文本");
  });
});
