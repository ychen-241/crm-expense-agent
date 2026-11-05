# CRM智能分析平台 · 评价与升级建议智能体系统

FastAPI（异步）+ RAG 报销制度问答 + 报销发起预校验。Python 3.11+。

四层架构：入口层（REST/JWT）→ 服务层（领域服务）→ 智能体编排层（编排器/RAG Agent/报销 Agent/LLM 适配层）→ 数据模型层（PostgreSQL + pgvector）。

## 快速开始

```bash
# 1. 起数据库（PostgreSQL + pgvector 扩展）
docker compose up -d

# 2. 安装依赖
python -m venv .venv
.venv\Scripts\activate            # Windows
pip install -e ".[dev]"

# 3. 配置 LLM 供应商
copy .env.example .env            # 填入 LLM_API_KEY 等

# 4. 启动（首次启动自动建表 + 种子账号 admin/employee）
uvicorn app.main:app --reload

# 5. 验证
#    http://127.0.0.1:8000/docs        Swagger UI
#    http://127.0.0.1:8000/health      健康检查
```

## 种子账号

| 角色 | 用户名 | 默认密码 | 能力 |
|---|---|---|---|
| 管理员 | admin | admin123 | 上传/停用制度文档、查看全部记录 |
| 员工 | employee | employee123 | 制度问答、发起报销 |

## 第一周验证剧本

1. 管理员登录 → `POST /api/v1/kb/documents` 上传 `knowledge/差旅费报销制度.md`
2. 员工登录 → `POST /api/v1/chat` 提问"出差住宿标准是多少" → 返回带引用的回答
3. 员工 → `POST /api/v1/reimbursements` 提交一笔超标报销 → AI 预校验给出制度依据
4. 管理员 → `GET /api/v1/kb/records` 查看问答与报销记录

## 换 LLM 供应商

只改 `.env`：`LLM_PROVIDER=dashscope` + 对应 `LLM_BASE_URL / LLM_CHAT_MODEL / LLM_EMBED_MODEL / EMBEDDING_DIM`。业务代码零改动（走 OpenAI 兼容协议）。

## 目录速览

```
app/
├── core/       # 配置、JWT、LLM 适配层（可替换供应商）
├── api/v1/     # 路由：auth / chat / reimburse / kb_admin
├── services/   # 领域服务（用户/会话/报销单/知识库）
├── agents/     # 编排器 + RAG Agent + 报销 Agent + prompts/
├── retrieval/  # Embedding + pgvector 向量检索
├── models/     # SQLAlchemy ORM（7 张表）
├── schemas/    # Pydantic 请求/响应模型
└── db/         # 异步 engine / session
```

> 说明：第一周骨架用 `create_all` 建表；表结构稳定后引入 Alembic 迁移（`app/db/migrations/`）。
