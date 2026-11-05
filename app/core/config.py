from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """集中配置：环境变量 / .env 覆盖默认值。"""

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    APP_NAME: str = "CRM智能分析平台-评价与升级建议智能体系统"

    # 数据库
    DATABASE_URL: str = "postgresql+asyncpg://crm:crm_secret@localhost:5432/crm_agent"

    # 认证
    JWT_SECRET: str = "dev-secret-change-me"
    JWT_EXPIRE_MINUTES: int = 720

    # LLM（OpenAI 兼容协议；换供应商只改这里）
    LLM_PROVIDER: str = "openai"  # openai | dashscope
    LLM_API_KEY: str = ""
    LLM_BASE_URL: str = "https://api.openai.com/v1"
    LLM_CHAT_MODEL: str = "gpt-4o-mini"
    LLM_EMBED_MODEL: str = "text-embedding-3-small"
    EMBEDDING_DIM: int = 1536

    # 检索与切片
    RETRIEVAL_TOP_K: int = 5
    CHUNK_SIZE: int = 500
    CHUNK_OVERLAP: int = 50

    # 种子账号
    ADMIN_USERNAME: str = "admin"
    ADMIN_PASSWORD: str = "admin123"
    EMPLOYEE_USERNAME: str = "employee"
    EMPLOYEE_PASSWORD: str = "employee123"

    # 知识库文件存储目录
    KNOWLEDGE_DIR: str = "knowledge/uploads"


@lru_cache
def get_settings() -> Settings:
    return Settings()
