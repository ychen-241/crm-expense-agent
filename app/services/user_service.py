"""用户与权限服务。"""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.security import hash_password
from app.models import User


async def get_by_username(db: AsyncSession, username: str) -> User | None:
    return (await db.execute(select(User).where(User.username == username))).scalar_one_or_none()


async def seed_default_users(db: AsyncSession) -> None:
    """首次启动创建种子账号（管理员 + 员工），已存在则跳过。"""
    s = get_settings()
    seeds = [
        (s.ADMIN_USERNAME, s.ADMIN_PASSWORD, "admin"),
        (s.EMPLOYEE_USERNAME, s.EMPLOYEE_PASSWORD, "employee"),
    ]
    changed = False
    for username, password, role in seeds:
        if await get_by_username(db, username) is None:
            db.add(User(username=username, password_hash=hash_password(password), role=role))
            changed = True
    if changed:
        await db.commit()
