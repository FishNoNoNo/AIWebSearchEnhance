# API 文档

服务启动后可以访问 `/docs` 查看 FastAPI 自动生成的 OpenAPI 文档。

## 初始化客户端

`POST /v1/client/init`

```json
{
  "api_key": "sk-xxx",
  "base_url": "https://api.openai.com/v1",
  "model": "gpt-4o-mini",
  "provider": "openai"
}
```

## 对话

`POST /v1/chat/completions`

请求体兼容 OpenAI Chat Completions，并扩展了 `client_id` 和 `search_options`。

```json
{
  "client_id": "cli_xxx",
  "messages": [{"role": "user", "content": "今天北京天气怎么样？"}],
  "search_options": {
    "force_search": true,
    "engine": "auto",
    "max_results": 5
  }
}
```

## 搜索

`POST /v1/search`

```json
{
  "query": "OpenAI latest model",
  "engine": "auto",
  "max_results": 5
}
```
