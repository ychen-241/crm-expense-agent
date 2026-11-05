"""编排器：意图识别 + 路由到对应 Agent（骨架版用关键词规则，后续可换 LLM 意图分类）。"""

import re

from sqlalchemy.ext.asyncio import AsyncSession

from app.agents import reimburse_agent, rag_agent
from app.models import User
from app.services import session_service

_REIMBURSE_KEYWORDS = ("报销", "发票", "申请单", "费用申请", "提交费用")


def detect_intent(content: str) -> str:
    """qa = 制度问答；reimburse = 报销发起/咨询。"""
    return "reimburse" if any(k in content for k in _REIMBURSE_KEYWORDS) else "qa"


async def handle(db: AsyncSession, user: User, session_id: int | None, content: str) -> dict:
    """处理一条员工消息：落库 → 路由 → 生成回答 → 回写。返回统一结构。"""
    if session_id is not None:
        chat_session = await session_service.get_own_session(db, session_id, user.id)
        if chat_session is None:
            raise ValueError("会话不存在或不属于当前用户")
    else:
        chat_session = await session_service.create_session(db, user.id, title=content[:20])

    await session_service.add_message(db, chat_session.id, "user", content)

    intent = detect_intent(content)
    citations: list[dict] = []
    if intent == "reimburse":
        parsed = reimburse_agent.parse_from_text(content)
        if parsed:
            check = reimburse_agent.pre_check(**parsed)
            reply = reimburse_agent.format_reply(parsed, check)
        else:
            reply = (
                "识别到报销意图，但未能从消息中解析出金额和类别。"
                "请通过 POST /api/v1/reimbursements 提交（需包含金额、类别、事由），"
                "或在消息中直接说明，例如：\"我要报销 800 元的酒店住宿\"。"
            )
    else:
        reply, citations = await rag_agent.answer(db, content)

    msg = await session_service.add_message(db, chat_session.id, "assistant", reply, citations or None)
    return {
        "session_id": chat_session.id,
        "message_id": msg.id,
        "intent": intent,
        "answer": reply,
        "citations": citations,
    }


_AMOUNT_RE = re.compile(r"(?:[¥￥]\s*(\d+(?:\.\d+)?)|(\d+(?:\.\d+)?)\s*元)")


def extract_amount(content: str) -> float | None:
    m = _AMOUNT_RE.search(content)
    if m is None:
        return None
    return float(m.group(1) or m.group(2))
