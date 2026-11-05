from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.agents import orchestrator
from app.api.deps import get_current_user
from app.db.session import get_db
from app.models import User
from app.schemas import ChatRequest, ChatResponse, MessageOut, SessionCreate, SessionOut
from app.services import session_service

router = APIRouter(prefix="/chat", tags=["chat"])


@router.post("/sessions", response_model=SessionOut)
async def create_session(
    body: SessionCreate, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)
) -> SessionOut:
    s = await session_service.create_session(db, user.id, body.title)
    return SessionOut(id=s.id, title=s.title, created_at=s.created_at)


@router.get("/sessions", response_model=list[SessionOut])
async def list_sessions(user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    return await session_service.list_sessions(db, user.id)


@router.get("/sessions/{session_id}/messages", response_model=list[MessageOut])
async def list_messages(
    session_id: int, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)
):
    session = await session_service.get_own_session(db, session_id, user.id)
    if session is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "会话不存在")
    return await session_service.list_messages(db, session_id)


@router.post("", response_model=ChatResponse)
async def chat(
    body: ChatRequest, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)
) -> ChatResponse:
    """员工问答统一入口：编排器做意图路由（制度问答 / 报销预校验）。"""
    try:
        result = await orchestrator.handle(db, user, body.session_id, body.content)
    except ValueError as e:
        raise HTTPException(status.HTTP_404_NOT_FOUND, str(e)) from None
    return ChatResponse(**result)
