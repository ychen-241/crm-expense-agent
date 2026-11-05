# 迁移目录（预留）

第一周骨架使用 `Base.metadata.create_all` 自动建表，暂不启用迁移。

表结构稳定后的接入步骤：

```bash
alembic init app/db/migrations       # 生成 env.py / versions/
# env.py 中 target_metadata 指向 app.models.Base.metadata，
# sqlalchemy.url 从 app.core.config 读取
alembic revision --autogenerate -m "init schema"
alembic upgrade head
```
