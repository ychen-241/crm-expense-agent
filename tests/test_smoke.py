"""冒烟测试：不依赖数据库与外部 LLM，只验证应用可装配、路由与纯逻辑正确。"""


def test_app_routes_registered():
    from app.main import app

    paths = set(app.openapi()["paths"])
    assert "/health" in paths
    assert "/api/v1/auth/login" in paths
    assert "/api/v1/chat" in paths
    assert "/api/v1/reimbursements" in paths
    assert "/api/v1/kb/documents" in paths
    assert "/api/v1/kb/records" in paths


def test_password_hash_roundtrip():
    from app.core.security import hash_password, verify_password

    stored = hash_password("s3cret")
    assert verify_password("s3cret", stored)
    assert not verify_password("wrong", stored)


def test_jwt_roundtrip():
    from app.core.security import create_access_token, decode_token

    token = create_access_token("alice", "admin")
    payload = decode_token(token)
    assert payload["sub"] == "alice"
    assert payload["role"] == "admin"


def test_intent_detection():
    from app.agents.orchestrator import detect_intent

    assert detect_intent("出差住宿标准是多少") == "qa"
    assert detect_intent("我要报销 800 元酒店住宿") == "reimburse"


def test_amount_extraction():
    from app.agents.orchestrator import extract_amount

    assert extract_amount("我要报销 800 元酒店住宿") == 800.0
    assert extract_amount("花了￥66.5打车") == 66.5
    assert extract_amount("住宿标准是多少") is None


def test_reimburse_pre_check():
    from app.agents.reimburse_agent import pre_check

    ok = pre_check(500, "住宿", "出差住宿")
    assert ok["passed"] is True

    over = pre_check(800, "住宿", "出差住宿")
    assert over["passed"] is False
    assert over["violations"][0]["rule"] == "single_limit"

    unknown = pre_check(100, "礼品", "送客户")
    assert unknown["passed"] is False
