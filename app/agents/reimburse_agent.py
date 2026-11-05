"""报销 Agent：从文本解析报销要素 + 按制度规则预校验（规则引擎骨架版）。"""

# 单次报销上限（元）。骨架版内置；后续改为从制度文档结构化抽取或管理端可配。
CATEGORY_LIMITS: dict[str, float] = {
    "住宿": 600.0,
    "交通": 800.0,
    "餐饮": 200.0,
    "办公": 500.0,
    "培训": 3000.0,
}

_CATEGORY_KEYWORDS = {
    "住宿": ("住宿", "酒店", "宾馆"),
    "交通": ("交通", "机票", "火车", "打车", "高铁"),
    "餐饮": ("餐饮", "餐", "招待"),
    "办公": ("办公", "耗材", "文具"),
    "培训": ("培训", "课程", "考试"),
}


def detect_category(content: str) -> str | None:
    for category, keywords in _CATEGORY_KEYWORDS.items():
        if any(k in content for k in keywords):
            return category
    return None


def parse_from_text(content: str) -> dict | None:
    """从自然语言解析 {amount, category, reason}；解析失败返回 None。"""
    from app.agents.orchestrator import extract_amount

    amount = extract_amount(content)
    if amount is None:
        return None
    category = detect_category(content) or "其他"
    return {"amount": amount, "category": category, "reason": content.strip()}


def pre_check(amount: float, category: str, reason: str = "") -> dict:
    """对照单次上限规则做预校验，返回可落库的 ai_check_result。"""
    violations: list[dict] = []
    limit = CATEGORY_LIMITS.get(category)
    if limit is None:
        violations.append({"rule": "category_known", "message": f"类别「{category}」无既定限额，请人工复核"})
    elif amount > limit:
        violations.append({
            "rule": "single_limit",
            "message": f"金额 {amount} 元超过「{category}」类单次上限 {limit} 元",
        })
    if not reason.strip():
        violations.append({"rule": "reason_required", "message": "缺少报销事由，请补充说明"})

    advice = (
        "请补充事由或调低金额后重新提交。" if violations
        else "符合现行制度限额，请上传对应发票后提交审批。"
    )
    return {"passed": not violations, "violations": violations, "advice": advice}


def format_reply(parsed: dict, check: dict) -> str:
    lines = [f"已按制度对你的报销预校验（{parsed['category']} · {parsed['amount']} 元）："]
    if check["passed"]:
        lines.append("✅ 校验通过。" + check["advice"])
    else:
        lines.append("⚠️ 存在以下问题：")
        lines.extend(f"- {v['message']}" for v in check["violations"])
        lines.append(check["advice"])
    lines.append("确认无误可调用 POST /api/v1/reimbursements 正式提交。")
    return "\n".join(lines)
