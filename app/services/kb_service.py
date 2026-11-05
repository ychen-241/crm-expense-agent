"""知识库服务：上传 → 解析 → 切片 → 向量化 → 入库，以及文档停用/列表。"""

from pathlib import Path

from fastapi import HTTPException, UploadFile
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.models import AuditLog, KBChunk, KBDocument, User
from app.retrieval.embedder import embed_texts

_SUFFIXES = {".md": "md", ".txt": "txt"}


def _chunk_text(text: str, size: int, overlap: int) -> list[str]:
    """按字符数滑动窗口切片（骨架版；后续可升级为按标题/语义切片）。"""
    text = text.strip()
    if not text:
        return []
    step = max(size - overlap, 1)
    return [text[i : i + size] for i in range(0, len(text), step)]


async def ingest_document(db: AsyncSession, file: UploadFile, user: User) -> KBDocument:
    settings = get_settings()
    suffix = Path(file.filename or "").suffix.lower()
    if suffix not in _SUFFIXES:
        raise HTTPException(415, f"骨架版仅支持 md/txt，收到：{suffix or '(无后缀)'}")

    raw = await file.read()
    text = raw.decode("utf-8", errors="ignore")
    if not text.strip():
        raise HTTPException(400, "文档内容为空")

    # 落盘留档
    upload_dir = Path(settings.KNOWLEDGE_DIR)
    upload_dir.mkdir(parents=True, exist_ok=True)
    save_path = upload_dir / (file.filename or "untitled" + suffix)
    save_path.write_bytes(raw)

    doc = KBDocument(
        title=Path(file.filename).stem,
        file_path=str(save_path),
        file_type=_SUFFIXES[suffix],
        status="processing",
        uploaded_by=user.id,
    )
    db.add(doc)
    await db.flush()

    contents = _chunk_text(text, settings.CHUNK_SIZE, settings.CHUNK_OVERLAP)
    vectors = await embed_texts(contents)
    for idx, (content, vec) in enumerate(zip(contents, vectors, strict=True)):
        db.add(KBChunk(document_id=doc.id, content=content, embedding=vec, chunk_index=idx))
    doc.status = "active"

    db.add(AuditLog(user_id=user.id, action="kb.upload", target_type="kb_document", target_id=str(doc.id),
                    detail={"filename": file.filename, "chunks": len(contents)}))
    await db.commit()
    await db.refresh(doc)
    return doc


async def disable_document(db: AsyncSession, doc_id: int, user: User) -> KBDocument | None:
    doc = (await db.execute(select(KBDocument).where(KBDocument.id == doc_id))).scalar_one_or_none()
    if doc is None:
        return None
    doc.status = "disabled"
    db.add(AuditLog(user_id=user.id, action="kb.disable", target_type="kb_document", target_id=str(doc_id)))
    await db.commit()
    await db.refresh(doc)
    return doc


async def list_documents(db: AsyncSession) -> list[dict]:
    stmt = select(KBDocument).order_by(KBDocument.id.desc())
    docs = (await db.execute(stmt)).scalars().all()
    counts = dict(
        (await db.execute(
            select(KBChunk.document_id, func.count()).group_by(KBChunk.document_id)
        )).all()
    )
    return [
        {
            "id": d.id, "title": d.title, "file_type": d.file_type, "version": d.version,
            "status": d.status, "chunk_count": counts.get(d.id, 0), "created_at": d.created_at,
        }
        for d in docs
    ]
