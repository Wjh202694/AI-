# -*- coding: utf-8 -*-
"""FastAPI 应用：检索 API + 静态托管。"""

from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import FileResponse, JSONResponse, PlainTextResponse
from fastapi.staticfiles import StaticFiles


class NoCacheStaticFiles(StaticFiles):
    """StaticFiles 子类，强制设置 no-cache 响应头，避免旧代码被缓存。"""
    async def get_response(self, path, scope):
        resp = await super().get_response(path, scope)
        resp.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
        resp.headers["Pragma"] = "no-cache"
        resp.headers["Expires"] = "0"
        return resp


class NoCacheFileResponse(FileResponse):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
        self.headers["Pragma"] = "no-cache"
        self.headers["Expires"] = "0"

from . import aggregator, clicks, history
from . import llm as llm_mod
from .config import FRONTEND_DIR
from .models import (PlanRequest, PlanResponse, SearchRequest, SearchResponse, LLMRequest, ClickRequest)
from .query_planner import make_plan, extract_terms
from .clarifier import build_clarify

app = FastAPI(title="搜绎", docs_url=None, redoc_url=None)


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Pydantic 校验失败 → 返回明文，不再丢个 JSON 数组给前端。

    例如:
    [{"type":"missing","loc":["body","question"],"msg":"Field required"}]
    → "body.question: Field required"
    """
    parts = []
    for e in exc.errors():
        loc = ".".join(str(p) for p in e.get("loc", []))
        parts.append(f"{loc}: {e.get('msg', '')}")
    msg = "；".join(parts) if parts else "请求参数错误"
    return JSONResponse(status_code=400, content={"detail": msg})


@app.on_event("startup")
def startup():
    history.init_db()
    clicks.init_db()


@app.post("/api/plan", response_model=PlanResponse)
def api_plan(req: PlanRequest):
    question = req.question.strip()
    if not question:
        raise HTTPException(400, "问题不能为空")
    # 追问基于未调整的原始拆词，保证选项稳定
    base_terms, base_jargon = extract_terms(question, req.extra_terms)
    clarify = build_clarify(question, base_terms, base_jargon)
    terms, jargon, queries = make_plan(question, req.extra_terms, req.answers or None)
    return PlanResponse(question=question, terms=terms, jargon=jargon,
                        queries=queries, clarify=clarify, refined=bool(req.answers))


@app.post("/api/llm", response_model=dict)
async def api_llm(req: LLMRequest):
    """可选 LLM 增强：返回改写后的推荐检索式；未配置时 available=False。"""
    if not llm_mod.is_configured():
        return {"available": False, "query": None}
    q = await llm_mod.enhance(req.question, req.terms)
    return {"available": True, "query": q}


@app.post("/api/search", response_model=SearchResponse)
async def api_search(req: SearchRequest):
    question = req.question.strip()
    if not question:
        raise HTTPException(400, "问题不能为空")
    checked = [q for q in req.queries if q.checked]
    if not checked:
        raise HTTPException(400, "请至少勾选一条查询")
    try:
        results, status, stats, meta = await aggregator.aggregate(
            question, req.queries,
            terms=req.terms,
            relevance_tier=req.relevance_tier,
            relax_threshold=req.relax_threshold,
        )
    except ValueError as e:
        raise HTTPException(400, str(e))
    except Exception as e:
        # 兜底：任何 aggregator 异常都返回 500 但带明文详情
        raise HTTPException(500, f"聚合异常：{type(e).__name__}: {str(e)[:200]}")
    sid = history.save_search(question, req.queries, results, req.llm_used)
    return SearchResponse(
        search_id=sid, question=question, results=results,
        status=status, stats=stats,
        ask_relax=meta.get("ask_relax", False),
        relax_threshold=meta.get("relax_threshold", 0.0),
        relevance_tier=meta.get("relevance_tier", ""),
        filtered_total=meta.get("filtered_total", 0),
    )


@app.post("/api/click")
def api_click(req: ClickRequest):
    """埋点：用户点击搜索结果链接时上报一次。"""
    count = clicks.record_click(req.url)
    return {"ok": True, "url": req.url, "count": count}


@app.get("/api/history")
def api_history():
    return {"items": history.list_searches()}


@app.get("/api/history/{search_id}")
def api_history_detail(search_id: int):
    data = history.get_search(search_id)
    if not data:
        raise HTTPException(404, "记录不存在")
    return data


@app.get("/api/export/{search_id}", response_class=PlainTextResponse)
def api_export(search_id: int):
    md = history.export_markdown(search_id)
    if md is None:
        raise HTTPException(404, "记录不存在")
    return md


@app.get("/api/health")
def api_health():
    return {"ok": True}


@app.get("/")
def index():
    return NoCacheFileResponse(str(FRONTEND_DIR / "index.html"))


app.mount("/static", NoCacheStaticFiles(directory=str(FRONTEND_DIR)), name="static")
