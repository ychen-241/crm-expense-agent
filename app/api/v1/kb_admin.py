"""管理员接口：知识库维护 + 全量记录查看。"""

from fastapi import APIRouter, Depends, HTTPException, UploadFile, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import require_admin
from app.db.session import get_db
from app.models import ChatSession, User
from app.schemas import AdminRecordsOut, KBDocumentOut, ReimburseOut, SessionOut
from app.services import kb_service, reimbursement_service, session_service

router = APIRouter(prefix="/kb", tags=["kb-admin"])


@router.post("/documents", response_model=KBDocumentOut)
async def upload_document(
    file: UploadFile,
    user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """上传报销制度文档（md/txt）：切片 + 向量化后即刻可检索。"""
    doc = await kb_service.ingest_document(db, file, user)
    docs = await kb_service.list_documents(db)
    return next(d for d in docs if d["id"] == doc.id)


@router.get("/documents", response_model=list[KBDocumentOut])
async def list_documents(user: User = Depends(require_admin), db: AsyncSession = Depends(get_db)):
    return await kb_service.list_documents(db)


@router.delete("/documents/{doc_id}", response_model=KBDocumentOut)
async def disable_document(
    doc_id: int, user: User = Depends(require_admin), db: AsyncSession = Depends(get_db)
):
    """停用文档：不再参与检索，历史引用可溯源。"""
    doc = await kb_service.disable_document(db, doc_id, user)
    if doc is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "文档不存在")
    docs = await kb_service.list_documents(db)
    return next(d for d in docs if d["id"] == doc.id)


@router.get("/records", response_model=AdminRecordsOut)
async def view_records(user: User = Depends(require_admin), db: AsyncSession = Depends(get_db)):
    """查看全员问答会话与报销记录。"""
    sessions = list(
        (await db.execute(select(ChatSession).order_by(ChatSession.id.desc()).limit(50))).scalars()
    )
    return AdminRecordsOut(
        recent_sessions=[SessionOut(id=s.id, title=s.title, created_at=s.created_at) for s in sessions],
        reimbursements=await reimbursement_service.list_all(db),
    )
