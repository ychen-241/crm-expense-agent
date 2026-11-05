"""Pydantic 请求/响应模型（v1 骨架集中在一个模块，规模大了再拆分）。"""

from datetime import datetime

from pydantic import BaseModel, Field, ConfigDict

_ORM = ConfigDict(from_attributes=True)


# ---- auth ----
class TokenOut(BaseModel):
    access_token: str
    token_type: str = "bearer"
    role: str


class UserOut(BaseModel):
    id: int
    username: str
    role: str
    dept: str | None = None


# ---- chat ----
class SessionCreate(BaseModel):
    title: str = "新会话"


class SessionOut(BaseModel):
    model_config = _ORM

    id: int
    title: str
    created_at: datetime


class MessageOut(BaseModel):
    model_config = _ORM

    id: int
    role: str
    content: str
    citations: list[dict] | None = None
    created_at: datetime


class ChatRequest(BaseModel):
    session_id: int | None = None
    content: str = Field(min_length=1, max_length=4000)


class ChatResponse(BaseModel):
    session_id: int
    message_id: int
    intent: str
    answer: str
    citations: list[dict] = []


# ---- knowledge base ----
class KBDocumentOut(BaseModel):
    id: int
    title: str
    file_type: str
    version: int
    status: str
    chunk_count: int = 0
    created_at: datetime


# ---- reimbursement ----
class ReimburseCreate(BaseModel):
    amount: float = Field(gt=0)
    category: str
    reason: str = ""


class ReimburseOut(BaseModel):
    model_config = _ORM

    id: int
    user_id: int
    amount: float
    category: str
    reason: str
    status: str
    ai_check_result: dict | None = None
    created_at: datetime


# ---- admin records ----
class AdminRecordsOut(BaseModel):
    recent_sessions: list[SessionOut]
    reimbursements: list[ReimburseOut]
