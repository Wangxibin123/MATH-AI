"""
真实 LLM Router：
   · 根据 agent 调用相应的 LLM API
   · 使用 Pydantic Schema 校验响应
   · 返回 (payload, model_used, usage) 三元组
"""

from __future__ import annotations

import json
import logging
from typing import Any, Dict, Tuple, List

import openai
from openai import OpenAI

from apps.gateway.schemas.agents import SCHEMA_MAP
from apps.gateway.settings import settings
from packages.prompt_engine import build_prompt

logger = logging.getLogger(__name__)

# 初始化 OpenAI 客户端
client = OpenAI(api_key=settings.OPENAI_API_KEY)

# 默认使用的模型
DEFAULT_MODEL = "gpt-4.5-preview"

# 每个 agent 对应的函数调用定义
FUNCTION_DEFINITIONS = {
    "problem_ingest": {
        "name": "problem_ingest",
        "description": "解析数学问题并生成第一步",
        "parameters": {
            "type": "object",
            "properties": {
                "rawLatex": {"type": "string", "description": "原始 LaTeX 文本"},
                "firstStep": {
                    "type": "object",
                    "properties": {
                        "latex": {"type": "string", "description": "第一步的 LaTeX"},
                        "explanation": {"type": "string", "description": "第一步的解释"}
                    },
                    "required": ["latex", "explanation"]
                },
                "problemTask": {"type": "string", "description": "问题任务描述"}
            },
            "required": ["rawLatex", "firstStep", "problemTask"]
        }
    },
    "latex_refine": {
        "name": "latex_refine",
        "description": "优化 LaTeX 表达式",
        "parameters": {
            "type": "object",
            "properties": {
                "latex": {"type": "string", "description": "优化后的 LaTeX"}
            },
            "required": ["latex"]
        }
    },
    "suggest_next_moves": {
        "name": "suggest_next_moves",
        "description": "建议下一步可能的操作",
        "parameters": {
            "type": "object",
            "properties": {
                "suggestions": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "建议的下一步操作列表"
                }
            },
            "required": ["suggestions"]
        }
    },
    "solve_next_step": {
        "name": "solve_next_step",
        "description": "解决下一步",
        "parameters": {
            "type": "object",
            "properties": {
                "latex": {"type": "string", "description": "下一步的 LaTeX"},
                "explanation": {"type": "string", "description": "步骤解释"},
                "finished": {"type": "boolean", "description": "是否已经完成解题"}
            },
            "required": ["latex", "explanation", "finished"]
        }
    },
    "summarize_history": {
        "name": "summarize_history",
        "description": "总结解题历史",
        "parameters": {
            "type": "object",
            "properties": {
                "summary": {"type": "string", "description": "历史总结"}
            },
            "required": ["summary"]
        }
    },
    "explain_step": {
        "name": "explain_step",
        "description": "解释当前步骤的推导过程",
        "parameters": {
            "type": "object",
            "properties": {
                "explanation": {"type": "string", "description": "详细的推导解释"}
            },
            "required": ["explanation"]
        }
    },
    "verify_step_forward": {
        "name": "verify_step_forward",
        "description": "验证当前步骤是否可以从历史步骤正确推导",
        "parameters": {
            "type": "object",
            "properties": {
                "is_correct": {"type": "boolean", "description": "步骤是否正确"},
                "explanation": {"type": "string", "description": "验证解释"},
                "error_reason": {"type": "string", "description": "如果错误，说明原因"}
            },
            "required": ["is_correct", "explanation"]
        }
    },
    "verify_step_backward": {
        "name": "verify_step_backward",
        "description": "验证当前步骤是否可以推导出后续步骤",
        "parameters": {
            "type": "object",
            "properties": {
                "is_correct": {"type": "boolean", "description": "步骤是否正确"},
                "explanation": {"type": "string", "description": "验证解释"},
                "error_reason": {"type": "string", "description": "如果错误，说明原因"}
            },
            "required": ["is_correct", "explanation"]
        }
    }
}

async def call(
    agent: str,
    ctx: Dict[str, Any] | None = None,
) -> Tuple[Dict[str, Any], str, Dict[str, int]]:
    """
    调用真实 LLM 的统一异步接口
    :returns: (payload, model_used, usage)
    """
    ctx = ctx or {}

    if agent not in SCHEMA_MAP:
        raise ValueError(f"unknown agent '{agent}'")

    # 1) 生成 prompt
    messages = build_prompt(agent, ctx)

    print(ctx)

    # 2) 调用 OpenAI API
    try:
        response = client.chat.completions.create(
            model=DEFAULT_MODEL,
            messages=messages,
            functions=[FUNCTION_DEFINITIONS[agent]],
            function_call={"name": agent},
            temperature=0.7,
        )
    except Exception as e:
        logger.error(f"OpenAI API call failed: {e}")
        raise

    # 3) 解析响应
    try:
        function_call = response.choices[0].message.function_call
        if not function_call or function_call.name != agent:
            raise ValueError(f"Unexpected function call: {function_call}")
        
        raw = json.loads(function_call.arguments)
    except Exception as e:
        logger.error(f"Failed to parse OpenAI response: {e}")
        raise

    # 4) Schema 校验
    try:
        payload = SCHEMA_MAP[agent](**raw).model_dump()
    except Exception as e:
        logger.error(f"Schema validation failed: {e}")
        raise

    # 5) 返回结果
    usage = {
        "prompt_tokens": response.usage.prompt_tokens,
        "completion_tokens": response.usage.completion_tokens,
        "total_tokens": response.usage.total_tokens,
    }
    model_tag = response.model

    logger.debug("LLM-real %s -> %s", agent, payload)
    return payload, model_tag, usage

async def solve_complete(ctx: Dict[str, Any]) -> Tuple[Dict[str, Any], str, Dict[str, int]]:
    """
    完整解题流程：
    1. 解析题目 (problem_ingest)
    2. 循环执行：
       - 建议下一步 (suggest_next_moves)
       - 执行下一步 (solve_next_step)
       - 直到完成或无法继续
    """
    if "raw_text" not in ctx:
        raise ValueError("raw_text is required")

    # 初始化总使用量
    total_usage = {
        "prompt_tokens": 0,
        "completion_tokens": 0,
        "total_tokens": 0
    }

    # 1. 解析题目
    ingest_payload, model, usage = await call("problem_ingest", ctx)
    current_latex = ingest_payload["firstStep"]["latex"]
    raw_latex = ingest_payload["rawLatex"]
    
    # 累加使用量
    for key in total_usage:
        total_usage[key] += usage[key]
    
    # 2. 循环解题
    history = [
        {
            "latex": current_latex,
            "explanation": "原始方程"
        }
    ]
    
    max_steps = 10  # 防止无限循环
    for step in range(max_steps):
        # 2.1 建议下一步
        suggest_payload, model, usage = await call("suggest_next_moves", {
            "rawLatex": raw_latex,
            "recent_steps": history
        })
        
        # 累加使用量
        for key in total_usage:
            total_usage[key] += usage[key]
        
        if not suggest_payload["suggestions"]:
            break
            
        # 2.2 执行下一步
        solve_payload, model, usage = await call("solve_next_step", {
            "rawLatex": raw_latex,
            "chosen_suggestion": suggest_payload["suggestions"][0],
            "suggest_source": "suggest_next_moves",
            "history_brief": "\n".join([f"{h['explanation']}: {h['latex']}" for h in history])
        })
        
        # 累加使用量
        for key in total_usage:
            total_usage[key] += usage[key]
        
        # 2.3 更新历史
        current_latex = solve_payload["latex"]
        history.append({
            "latex": current_latex,
            "explanation": solve_payload["explanation"]
        })
        
        # 2.4 检查是否完成
        if solve_payload["finished"]:
            break

    # 累加使用量
    for key in total_usage:
        total_usage[key] += usage[key]

    # 4. 返回完整结果
    return {
        "problem": ingest_payload['problemTask'],
        "steps": history,
    }, model, total_usage 