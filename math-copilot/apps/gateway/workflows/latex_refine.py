"""
W-02 手动修改题干 LaTeX
---------------------------------

场景：用户在前端手动把 `x+y` 改成 `\frac{x}{y}`。

只做两件事：
1. 调 BlockService.update() 记录修改；
2. 把修改记录发给 LLM，用于后续 Trace（Stub 里只是 no-op）。
"""

from __future__ import annotations

import uuid
from apps.gateway.services.block_service import BlockService
from apps.gateway.services.llm_router import call


async def run(block_id: str, new_latex: str, svc: BlockService):
    """
    Parameters
    ----------
    block_id : str
        被修改的块 ID。
    new_latex : str
        修改后的 LaTeX 字符串。
    svc : BlockService
        当前会话的 BlockService。

    Returns
    -------
    Block
        已更新后的块对象。
    """
    # ① 更新 DB（会触发 block_edit 事件）
    block_uuid = uuid.UUID(block_id)
    blk = svc.update(block_uuid, latex=new_latex)

    # ② 记录到 LLM（Stub 返回空占位）
    await call(
        "latex_refine",
        {"block_id": block_id, "new_latex": new_latex},
    )

    return blk
