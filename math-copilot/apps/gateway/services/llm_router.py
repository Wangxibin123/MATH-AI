"""
离线 Stub Router：
   · 根据 agent 返回一段"看起来合理"的假 JSON
   · 用 Pydantic Schema 校验，保证字段/类型正确
   · 返回 (payload, model_used, usage) 三元组，接口与未来真实模型保持一致
任何测试 / FastAPI 路由全都可直接调用。
"""

from __future__ import annotations

import logging
import random
from typing import Any, Dict, Tuple

from apps.gateway.schemas.agents import SCHEMA_MAP
from packages.prompt_engine import build_prompt  # 仅用于生成 prompt 方便调试

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------


def _fake_call(agent: str, ctx: Dict[str, Any]) -> Dict[str, Any]:
    """针对不同 agent 产出固定示例数据"""
    match agent:
        case "problem_ingest":
            return {
                "rawLatex": ctx.get("raw_text", "x+y"),
                "firstStep": {"latex": "x+y", "explanation": "去括号"},
                "problemTask": "化简",
            }
        case "latex_refine":
            return {"latex": ctx["rawLatex"].replace(" ", "")}
        case "block_parse":
            return {"explanation": "泰勒展开第一项", "children": []}
        case "suggest_next_moves":
            return {"suggestions": [ctx.get("currentLatex", "x") + "+1"]}
        case "solve_next_step":
            return {"latex": "x+1", "explanation": "加 1"}
        case "solve_to_end":
            return {"latex": "x+1", "explanation": "完成", "finished": True}
        case "summarize_history":
            return {"summary": "共 2 步，已完成"}
        case "answer_to_steps":
            return {"blocks": [{"latex": "x+1", "explanation": "末步"}]}
        case _:
            return {"altOutputs": []}


# ---------------------------------------------------------------------------


async def call(
    agent: str,
    ctx: Dict[str, Any] | None = None,
) -> Tuple[Dict[str, Any], str, Dict[str, int]]:
    """
    对外统一异步接口
    :returns: (payload, model_used, usage)
    """
    ctx = ctx or {}

    if agent not in SCHEMA_MAP:
        raise ValueError(f"unknown agent '{agent}'")

    # 1) 生成 prompt（仅日志观测，不真正发网络）
    _ = build_prompt(agent, ctx)

    # 2) 伪造响应
    raw = _fake_call(agent, ctx)

    # 3) Schema 校验（出错直接抛 Pydantic ValidationError）
    payload = SCHEMA_MAP[agent](**raw).model_dump()

    # 4) 返回 usage & model tag
    usage = {"prompt_tokens": 1, "completion_tokens": 1, "total_tokens": 2}
    model_tag = f"stub-{random.randint(0, 9)}"

    logger.debug("LLM-stub %s -> %s", agent, payload)
    return payload, model_tag, usage
