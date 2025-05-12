"""
W-01 题干上传 → 生成首块
-------------------------------------

调用链：

    Web / API 层
        │
        ▼
    await problem_ingest_run(...)
        │
        ├─ 1.  call("problem_ingest", ctx)  # Stub LLM
        └─ 2.  BlockService.create(...)

结果：返回 **首块 Block 实例**，orderIndex 必为 0。
"""

from __future__ import annotations

from apps.gateway.services.block_service import BlockService
from apps.gateway.services.llm_router import call  # ← 依旧是 stub，零网络


async def run(raw_text: str, svc: BlockService):
    """
    Parameters
    ----------
    raw_text : str
        用户上传的原始题干（纯文本或 OCR 结果）。
    svc : BlockService
        已注入 `problem_id` 的 BlockService 实例。
        由调用方负责：`svc.problem_id = <uuid>`。

    Returns
    -------
    Block
        首块对象，已写入数据库。
    """
    # 向 MyPy 确认 svc.problem_id 在此时不会是 None
    assert (
        svc.problem_id is not None
    ), "BlockService.problem_id must be set before calling problem_ingest_run"

    # ① 调 LLM Router —— stub 会返回固定示例
    payload, *_ = await call("problem_ingest", {"raw_text": raw_text})
    # e.g. payload = {"rawLatex": "x+y"}

    # ② 写入数据库
    blk = svc.create(
        problem_id=svc.problem_id,  # 必传
        latex=payload["rawLatex"],  # Stub 保证字段存在
    )
    return blk
