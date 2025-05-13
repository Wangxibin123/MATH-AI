from __future__ import annotations

from typing import Dict, Any

from fastapi import APIRouter, HTTPException, Body

from apps.gateway.services.llm_router import call as llm_call

router = APIRouter(prefix="/chat", tags=["LLM"])


@router.post("/{agent}", summary="LLM Agent 统一入口")
async def chat(agent: str, ctx: Dict[str, Any] = Body(...)) -> dict:
    """
    ctx 直接透传给 prompt_engine → router
    - agent == "problem_ingest" 时，必须携带 raw_text
    """
    # -------- 额外验证：raw_text 必填 --------
    if agent == "problem_ingest":
        if "raw_text" not in ctx or not ctx["raw_text"]:
            # 伪造 FastAPI 标准 422 格式，方便前端 / curl 脚本统一解析
            raise HTTPException(
                status_code=422,
                detail=[
                    {
                        "loc": ["body", "raw_text"],
                        "msg": "Field required",
                        "type": "missing",
                        "input": ctx,
                    }
                ],
            )

    # ---------- 业务调用 ----------
    try:
        payload, model, usage = await llm_call(agent, ctx)
    except ValueError as e:  # llm_router 的业务异常
        raise HTTPException(status_code=400, detail=str(e)) from e

    return {
        "payload": payload,
        "model": model,
        "usage": usage,
    }
