from fastapi import FastAPI

from apps.gateway.logging_setup import setup_logging  # Assuming this exists from v0.3.0-plus
from apps.gateway.settings import settings

# router 选择：stub or real（后续接真实模型再切）
if settings.USE_STUB:
    from apps.gateway.services.llm_router import call as llm_call_service  # noqa: F401
else:
    # This part is for future use, llm_router_real.py might not exist yet
    # or might need its own dependencies. For now, we assume it might raise
    # an ImportError if settings.USE_STUB is False and it's not implemented.
    try:
        from apps.gateway.services.llm_router_real import call as llm_call_service  # type: ignore # noqa: F401
    except ImportError:
        if not settings.USE_STUB:
            # Only raise error if we are explicitly trying to use the real router and it's not found
            raise ImportError("llm_router_real.py not found or not configured, but USE_STUB is False.")
        # If USE_STUB is True, we don't care if llm_router_real is missing for now.
        pass  # Or assign a placeholder if needed for type checking when USE_STUB=True

# -----------------------------------------------------------------------
setup_logging()  # Assuming this function is defined in logging_setup.py

app = FastAPI(title="Math Copilot API", description="API for Math Copilot services", version="0.3.1")

# @app.on_event("startup")
# async def on_startup():
#     # create_db_and_tables() # Removed as per v0.3.1 plan (handled by Alembic/seed)
#     pass

# 子路由
from apps.gateway.routers import llm as llm_router_definition  # noqa: E402

# app.include_router(blocks_router.router) # Removed blocks_router for v0.3.1
app.include_router(llm_router_definition.router)


@app.get("/", tags=["Root"])
async def read_root():
    return {"message": "Welcome to Math Copilot API v0.3.1"}
