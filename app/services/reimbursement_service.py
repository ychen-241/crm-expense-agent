"""报销单服务：发起、查询、状态流转。"""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Reimbursement


async def create(
    db: AsyncSession,
    user_id: int,
    amount: float,
    category: str,
    reason: str,
    ai_check_result: dict,
    status: str,
) -> Reimbursement:
    record = Reimbursement(
        user_id=user_id,
        amount=amount,
        category=category,
        reason=reason,
        ai_check_result=ai_check_result,
        status=status,
    )
    db.add(record)
    await db.commit()
    await db.refresh(record)
    return record


async def list_by_user(db: AsyncSession, user_id: int) -> list[Reimbursement]:
    stmt = select(Reimbursement).where(Reimbursement.user_id == user_id).order_by(Reimbursement.id.desc())
    return list((await db.execute(stmt)).scalars())


async def list_all(db: AsyncSession, limit: int = 100) -> list[Reimbursement]:
    stmt = select(Reimbursement).order_by(Reimbursement.id.desc()).limit(limit)
    return list((await db.execute(stmt)).scalars())
