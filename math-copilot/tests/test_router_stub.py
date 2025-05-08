import pytest

from apps.gateway.services.llm_router import call

AGENTS = [
    "problem_ingest",
    "latex_refine",
    "block_parse",
    "suggest_next_moves",
    "solve_next_step",
    "solve_to_end",
    "summarize_history",
    "answer_to_steps",
]

BASE_CTX = {
    "raw_text": "y=x",
    "rawLatex": "x",
    "currentLatex": "x",
    "recent_steps": "Step 1: Do this.",
    "suggest_source": "user",
    "all_steps": "Step 1: ...\nStep 2: ...",
    "answer_raw": "The answer is x=1",
    "chosen_suggestion": "Let's try x+1",
    "history_brief": "Previously, we did y.",
}


@pytest.mark.asyncio
@pytest.mark.parametrize("agent", AGENTS)
async def test_stub_router_schema(agent: str) -> None:
    payload, model, usage = await call(agent, ctx=dict(BASE_CTX))
    assert model.startswith("stub-")
    assert usage["total_tokens"] == 2
    # 简单断言：payload 至少有一个 key
    assert isinstance(payload, dict) and payload
