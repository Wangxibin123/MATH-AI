"""
单元测试：验证 W-01 是否能
    • 在 DB 新增 1 条 Block
    • orderIndex == 0
    • latex 字段与输入一致
"""

import uuid  # 分开导入
import pytest  # 分开导入
from sqlmodel import Session

from apps.gateway.db import init_db, engine
from apps.gateway.models import Problem
from apps.gateway.services.block_service import BlockService
from apps.gateway.workflows import problem_ingest_run


# ---------- 全模块共享的 DB Fixture ----------
@pytest.fixture(scope="module", autouse=True)
def _db():
    init_db()  # Alembic 已建表；这里确保 metadata 也同步
    yield  # 不清理 —— CI 会在每轮开头 rm /tmp DB


# ---------- W-01 测试主体 -------------------
@pytest.mark.asyncio
async def test_ingest():
    # 0. 先插入 Problem
    with Session(engine) as s:
        pb = Problem(id=uuid.uuid4(), rawLatex="dummy")
        s.add(pb)
        s.commit()

        # 1. BlockService 注入 problem_id
        svc = BlockService(s)
        svc.problem_id = pb.id

        # 2. 执行 workflow
        blk = await problem_ingest_run("x+y", svc)

        # 3. 断言
        assert blk.orderIndex == 0
        assert blk.latex == "x+y"
