"""
Pydantic 数据契约 —— Math-Copilot 9 个 Agent 的输入/输出 Schema
之后 FastAPI + OpenAI function-calling 都直接引用这里，保证单一真理源。
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


# 1. problem_ingest ---------------------------------------------------------
class _FirstStep(BaseModel):
    latex: str
    explanation: str


class ProblemIngest(BaseModel):
    rawLatex: str
    firstStep: Dict[str, str]
    problemTask: str


# 2. latex_refine -----------------------------------------------------------
class LatexRefine(BaseModel):
    latex: str


# 3. block_parse ------------------------------------------------------------
class BlockParse(BaseModel):
    explanation: str
    children: List[Dict[str, str]] = Field(default_factory=list)


# 4. suggest_next_moves -----------------------------------------------------
class SuggestNextMoves(BaseModel):
    suggestions: List[str]


# 5. solve_next_step --------------------------------------------------------
class SolveNextStep(BaseModel):
    latex: str
    explanation: str
    finished: bool


# 6. solve_to_end -----------------------------------------------------------
class SolveToEnd(SolveNextStep):
    finished: bool


# 7. summarize_history ------------------------------------------------------
class SummarizeHistory(BaseModel):
    summary: str


# 8. answer_to_steps --------------------------------------------------------
class _Step(BaseModel):
    latex: str
    explanation: str


class AnswerToSteps(BaseModel):
    blocks: List[_Step]


# 9. candidates (占位，后续做多模型打分) ------------------------------------
class Candidates(BaseModel):
    altOutputs: List[Dict[str, Any]]


# 10. explain_step -----------------------------------------------------------
class ExplainStep(BaseModel):
    explanation: str


# 11. verify_step_forward -----------------------------------------------------
class VerifyStepForward(BaseModel):
    is_correct: bool
    explanation: str
    error_reason: Optional[str] = None


# 12. verify_step_backward -----------------------------------------------------
class VerifyStepBackward(BaseModel):
    is_correct: bool
    explanation: str
    error_reason: Optional[str] = None


# ---- 映射表：名字即 Agent ID ----------------------------------------------
SCHEMA_MAP: dict[str, type[BaseModel]] = {
    "problem_ingest": ProblemIngest,
    "latex_refine": LatexRefine,
    "block_parse": BlockParse,
    "suggest_next_moves": SuggestNextMoves,
    "solve_next_step": SolveNextStep,
    "solve_to_end": SolveToEnd,
    "summarize_history": SummarizeHistory,
    "answer_to_steps": AnswerToSteps,
    "candidates": Candidates,
    "explain_step": ExplainStep,
    "verify_step_forward": VerifyStepForward,
    "verify_step_backward": VerifyStepBackward
}
