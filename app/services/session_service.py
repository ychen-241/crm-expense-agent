"""会话与消息服务：员工问答记录的留存与查询。"""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import ChatSession, Message


async def create_session(db: AsyncSession, user_id: int, title: str = "新会话") -> ChatSession:
    session = ChatSession(user_id=user_id, title=title)
    db.add(session)
    await db.commit()
    await db.refresh(session)
    return session


async def get_own_session(db: AsyncSession, session_id: int, user_id: int) -> ChatSession | None:
    stmt = select(ChatSession).where(ChatSession.id == session_id, ChatSession.user_id == user_id)
    return (await db.execute(stmt)).scalar_one_or_none()


async def list_sessions(db: AsyncSession, user_id: int) -> list[ChatSession]:
    stmt = select(ChatSession).where(ChatSession.user_id == user_id).order_by(ChatSession.id.desc())
    return list((await db.execute(stmt)).scalars())


async def list_messages(db: AsyncSession, session_id: int) -> list[Message]:
    stmt = select(Message).where(Message.session_id == session_id).order_by(Message.id)
    return list((await db.execute(stmt)).scalars())


async def add_message(
    db: AsyncSession,
    session_id: int,
    role: str,
    content: str,
    citations: list[dict] | None = None,
) -> Message:
    msg = Message(session_id=session_id, role=role, content=content, citations=citations)
    db.add(msg)
    await db.commit()
    await db.refresh(msg)
    return msg
