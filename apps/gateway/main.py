from fastapi import FastAPI

# Relative imports for DB setup and routers
from .db import create_db_and_tables
from .routers import blocks_router # Assuming blocks_router.py is in a 'routers' subdirectory

app = FastAPI(
    title="Math Copilot Gateway",
    description="API for Math Copilot services",
    version="0.1.0"
)

@app.on_event("startup")
def on_startup():
    # This will create database tables if they don't exist
    # when the application starts up.
    # For production, you'd typically use Alembic migrations.
    create_db_and_tables()

# Include the routers
# The router object is usually named 'router' in the file it's defined in.
app.include_router(blocks_router.router) 

@app.get("/", tags=["Root"])
async def read_root():
    return {"message": "Welcome to Math Copilot API"} 