from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.agents import reimburse_agent
from app.api.deps import get_current_user
from app.db.session import get_db
from app.models import User
from app.schemas import ReimburseCreate, ReimburseOut
from app.services import reimbursement_service

router = APIRouter(prefix="/reimbursements", tags=["reimburse"])


@router.post("", response_model=ReimburseOut)
async def create_reimbursement(
    body: ReimburseCreate, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)
) -> ReimburseOut:
    """发起报销：先由报销 Agent 按制度预校验，结论随单落库。"""
    check = reimburse_agent.pre_check(body.amount, body.category, body.reason)
    status = "submitted" if check["passed"] else "draft"
    record = await reimbursement_service.create(
        db, user.id, body.amount, body.category, body.reason, check, status
    )
    return record


@router.get("/mine", response_model=list[ReimburseOut])
async def list_mine(user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    return await reimbursement_service.list_by_user(db, user.id)
