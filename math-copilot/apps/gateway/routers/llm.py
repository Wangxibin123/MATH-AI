from fastapi import APIRouter, HTTPException

from apps.gateway.services.llm_router import call as llm_call

router = APIRouter(prefix="/chat", tags=["LLM"])


@router.post("/{agent}", summary="LLM Agent 统一入口")
async def chat(agent: str, ctx: dict) -> dict:
    """
    ctx 直接透传给 prompt_engine → router
    """
    try:
        payload, model, usage = await llm_call(agent, ctx)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return {"payload": payload, "model": model, "usage": usage}
