"""端到端演示脚本：登录 → 上传制度 → 员工问答 → 报销预校验 → 管理员看记录。

用法：先启动服务（uvicorn app.main:app --port 8000），再执行 python scripts/demo.py
"""

import sys
from pathlib import Path

import httpx

BASE = "http://127.0.0.1:8000"
DOC = Path(__file__).resolve().parent.parent / "knowledge" / "差旅费报销制度.md"


def login(client: httpx.Client, username: str, password: str) -> str:
    resp = client.post("/api/v1/auth/login", data={"username": username, "password": password})
    resp.raise_for_status()
    return resp.json()["access_token"]


def main() -> int:
    with httpx.Client(base_url=BASE, timeout=60) as client:
        # 1. 管理员上传制度文档
        admin_token = login(client, "admin", "admin123")
        admin_headers = {"Authorization": f"Bearer {admin_token}"}
        resp = client.post(
            "/api/v1/kb/documents",
            headers=admin_headers,
            files={"file": (DOC.name, DOC.read_bytes(), "text/markdown")},
        )
        print("① 上传制度文档:", resp.status_code, resp.json())
        resp.raise_for_status()

        # 2. 员工登录，制度问答
        emp_headers = {"Authorization": f"Bearer {login(client, 'employee', 'employee123')}"}
        resp = client.post(
            "/api/v1/chat", headers=emp_headers, json={"content": "出差住宿标准是多少"}
        )
        data = resp.json()
        print("\n② 制度问答:", data["intent"])
        print("   回答:", data["answer"].replace("\n", " / ")[:150])
        print("   引用:", [(c["document_title"], c["score"]) for c in data["citations"]])

        # 3. 聊天里表达报销意图（应触发预校验）
        resp = client.post(
            "/api/v1/chat", headers=emp_headers, json={"content": "我要报销 800 元酒店住宿"}
        )
        data = resp.json()
        print("\n③ 聊天报销意图:", data["intent"])
        print("   回答:", data["answer"].replace("\n", " / ")[:200])

        # 4. 正式发起报销（超标 → draft）
        resp = client.post(
            "/api/v1/reimbursements",
            headers=emp_headers,
            json={"amount": 800, "category": "住宿", "reason": "上海出差两晚"},
        )
        data = resp.json()
        print("\n④ 发起报销:", "id =", data["id"], "status =", data["status"])
        print("   AI 预校验:", data["ai_check_result"])

        # 5. 管理员查看记录
        resp = client.get("/api/v1/kb/records", headers=admin_headers)
        data = resp.json()
        print("\n⑤ 管理员看记录: 会话", len(data["recent_sessions"]), "条 / 报销单", len(data["reimbursements"]), "笔")

    print("\n全部演示通过 ✔")
    return 0


if __name__ == "__main__":
    sys.exit(main())
