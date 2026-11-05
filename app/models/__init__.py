"""ORM 模型：users / kb_documents / kb_chunks / sessions / messages / reimbursements / audit_logs。"""

from datetime import datetime
from typing import Any

from pgvector.sqlalchemy import Vector
from sqlalchemy import JSON, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.config import get_settings
from app.models.base import Base, TimestampMixin

_settings = get_settings()

# PostgreSQL 用 JSONB / pgvector；SQLite 演示模式自动降级为 JSON 列
FlexibleJSON = JSONB().with_variant(JSON(), "sqlite")
FlexibleVector = Vector(_settings.EMBEDDING_DIM).with_variant(JSON(), "sqlite")


class User(TimestampMixin, Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    username: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String(256))
    role: Mapped[str] = mapped_column(String(16), default="employee")  # employee | admin
    dept: Mapped[str | None] = mapped_column(String(64), nullable=True)


class KBDocument(TimestampMixin, Base):
    __tablename__ = "kb_documents"

    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(String(256))
    file_path: Mapped[str] = mapped_column(String(512))
    file_type: Mapped[str] = mapped_column(String(16))  # md | txt
    version: Mapped[int] = mapped_column(Integer, default=1)
    status: Mapped[str] = mapped_column(String(16), default="processing")  # processing | active | disabled
    uploaded_by: Mapped[int] = mapped_column(ForeignKey("users.id"))

    chunks: Mapped[list["KBChunk"]] = relationship(back_populates="document")


class KBChunk(TimestampMixin, Base):
    __tablename__ = "kb_chunks"

    id: Mapped[int] = mapped_column(primary_key=True)
    document_id: Mapped[int] = mapped_column(ForeignKey("kb_documents.id", ondelete="CASCADE"), index=True)
    content: Mapped[str] = mapped_column(Text)
    embedding: Mapped[Any] = mapped_column(FlexibleVector)
    chunk_index: Mapped[int] = mapped_column(Integer)

    document: Mapped["KBDocument"] = relationship(back_populates="chunks")


class ChatSession(TimestampMixin, Base):
    __tablename__ = "sessions"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    title: Mapped[str] = mapped_column(String(256), default="新会话")

    messages: Mapped[list["Message"]] = relationship(back_populates="session")


class Message(TimestampMixin, Base):
    __tablename__ = "messages"

    id: Mapped[int] = mapped_column(primary_key=True)
    session_id: Mapped[int] = mapped_column(ForeignKey("sessions.id", ondelete="CASCADE"), index=True)
    role: Mapped[str] = mapped_column(String(16))  # user | assistant
    content: Mapped[str] = mapped_column(Text)
    citations: Mapped[list[dict] | None] = mapped_column(FlexibleJSON, nullable=True)  # 命中的制度片段

    session: Mapped["ChatSession"] = relationship(back_populates="messages")


class Reimbursement(TimestampMixin, Base):
    __tablename__ = "reimbursements"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    amount: Mapped[float] = mapped_column()
    category: Mapped[str] = mapped_column(String(64))  # 住宿 | 交通 | 餐饮 | 办公 ...
    reason: Mapped[str] = mapped_column(Text, default="")
    status: Mapped[str] = mapped_column(String(16), default="submitted")  # draft | submitted | approved | rejected
    ai_check_result: Mapped[dict | None] = mapped_column(FlexibleJSON, nullable=True)  # 预校验结论


class AuditLog(TimestampMixin, Base):
    __tablename__ = "audit_logs"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    action: Mapped[str] = mapped_column(String(64))  # kb.upload / kb.disable / ...
    target_type: Mapped[str | None] = mapped_column(String(64), nullable=True)
    target_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    detail: Mapped[dict | None] = mapped_column(FlexibleJSON, nullable=True)


__all__ = [
    "AuditLog",
    "ChatSession",
    "KBChunk",
    "KBDocument",
    "Message",
    "Reimbursement",
    "User",
    "datetime",
]
