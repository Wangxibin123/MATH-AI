"""
W-03 解析块 → explanation
----------------------------

点击 "🪄解析" 按钮后触发。
"""

from __future__ import annotations

import uuid
from apps.gateway.services.block_service import BlockService
from apps.gateway.services.llm_router import call


async def run(block_id: str, svc: BlockService):
    """
    Parameters
    ----------
    block_id : str
        需要解析的块 ID。
    svc : BlockService
        BlockService 实例。

    Returns
    -------
    Block
        更新了 `explanation` 字段的块。
    """
    # ① 调 LLM（Stub）
    payload, *_ = await call("block_parse", {"block_id": block_id})
    # payload = {"explanation": "先化简再配方"}

    # ② 回写数据库
    block_uuid = uuid.UUID(block_id)
    blk = svc.update(block_uuid, explanation=payload["explanation"])
    return blk
