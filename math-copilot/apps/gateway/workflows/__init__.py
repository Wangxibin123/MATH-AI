"""
apps.gateway.workflows
======================

导出三个"一键调用"函数，给路由或其它服务层使用：

    from apps.gateway.workflows import (
        problem_ingest_run,
        latex_refine_run,
        block_parse_run,
    )

全部为 **`async def`**，所以上层应 `await` 调用。
"""

from .problem_ingest import run as problem_ingest_run
from .latex_refine import run as latex_refine_run
from .block_parse import run as block_parse_run

__all__ = [
    "problem_ingest_run",
    "latex_refine_run",
    "block_parse_run",
]
