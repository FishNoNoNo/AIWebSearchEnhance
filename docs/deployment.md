# 部署指南

## Docker Compose

```bash
cp .env.example .env
docker compose up --build
```

如果需要 Redis 缓存：

```bash
docker compose --profile redis up --build
```

同时把 `.env` 中的 `REDIS_ENABLED` 设为 `true`，并把 `config/config.yaml` 的 `cache.backend` 调整为 `redis`。

## 环境变量

- `ANALYSIS_API_KEY`：分析模型密钥，留空时使用启发式判断。
- `ORGANIZER_API_KEY`：整理模型密钥，留空时使用内置 Markdown 整理。
- `GOOGLE_API_KEY` / `GOOGLE_CX_ID`：Google Custom Search。
- `BING_API_KEY`：Bing Web Search。
- `SERPER_API_KEY`：Serper 搜索。
