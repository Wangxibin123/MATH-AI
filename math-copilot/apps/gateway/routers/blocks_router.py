from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session, select
from typing import List
import uuid

# Relative imports for models and db engine
from ..models import Block, BlockCreate, BlockRead
from ..db import engine

router = APIRouter(
    prefix="/blocks",
    tags=["Blocks"],
)

# Dependency to get a database session
def get_session():
    with Session(engine) as session:
        yield session

@router.post("/", response_model=BlockRead, status_code=status.HTTP_201_CREATED)
def create_block(*, session: Session = Depends(get_session), block_in: BlockCreate) -> Block:
    """
    Create a new block.
    """
    db_block = Block.from_orm(block_in)
    
    session.add(db_block)
    session.commit()
    session.refresh(db_block)
    return db_block

@router.get("/{block_id}", response_model=BlockRead)
def read_block(*, session: Session = Depends(get_session), block_id: uuid.UUID) -> Block:
    """
    Get a block by its ID.
    """
    db_block = session.get(Block, block_id)
    if not db_block:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Block not found")
    return db_block

@router.get("/", response_model=List[BlockRead])
def read_blocks(
    *, session: Session = Depends(get_session), skip: int = 0, limit: int = 100
) -> List[Block]:
    """
    Get a list of blocks, with pagination.
    """
    statement = select(Block).offset(skip).limit(limit)
    blocks = session.exec(statement).all()
    return blocks 