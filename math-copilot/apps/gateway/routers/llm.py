from __future__ import annotations

from typing import Dict, Any, List, Optional

from fastapi import APIRouter, HTTPException, Request, Body
from pydantic import BaseModel

from apps.gateway.services.llm_router_real import call as llm_call, solve_complete

router = APIRouter(prefix="/chat", tags=["chat"])

class Context(BaseModel):
    raw_text: Optional[str] = None
    currentLatex: Optional[str] = None
    suggestions: Optional[List[str]] = None
    history: Optional[List[Dict[str, str]]] = None
    rawLatex: Optional[str] = None
    all_steps: Optional[str] = None
    maxLen: Optional[int] = 200

@router.post("/solve_complete", summary="一次性解决整个题目")
async def solve_complete_endpoint(context: Context):
    """
    一次性解决整个题目的流程：
    1. 解析题目 (problem_ingest)
    2. 优化 LaTeX (latex_refine)
    3. 循环执行：
       - 建议下一步 (suggest_next_moves)
       - 执行下一步 (solve_next_step)
       - 直到完成或无法继续
    4. 总结历史 (summarize_history)
    """
    if not context.raw_text:
        raise HTTPException(status_code=422, detail="raw_text is required")
    
    try:
        payload, model, usage = await solve_complete({"raw_text": context.raw_text})
        return {
            "payload": payload,
            "model": model,
            "usage": usage
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/{agent}", summary="LLM Agent 统一入口")
async def agent_endpoint(agent: str, context: Dict[str, Any] = Body(...)):
    """
    统一的 LLM Agent 入口，根据 agent 参数调用不同的功能
    """
    try:
        payload, model, usage = await llm_call(agent, context)
        return {
            "payload": payload,
            "model": model,
            "usage": usage
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
